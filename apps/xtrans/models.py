#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.forms import ModelForm
from datetime import datetime
from rapidsms.message import Message
from rapidsms.connection import Connection

import textonic

class Translation(models.Model):
    """This model holds incoming messages and links to their respective translation
    method."""
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    received_at = models.DateTimeField(default=datetime.now)
    translated_at = models.DateTimeField(null=True)
    original_message = models.TextField(null=False) 
    translation_method = models.SlugField() #method being used
    translator_id = models.CharField(max_length=64, blank=True,null=True,default=None)
    translator_config = models.PositiveIntegerField(blank=True,null=True,default=None)
    translation = models.CharField(max_length=2000,null=True, default=None)

    @classmethod
    def has_been_translated(self):
        return self.translation != None

class MTurkConfig(models.Model):
    """This model contains the various fields for the Mechanical Turk configuration.
    It's a little awkward and could probably be simplified.  The basic concept is that 
    each message goes through two HITs.  In the first it is bundled with a number of
    other messages and sent as HIT in which workers are asked to translate each of the
    messages in the HIT.  Once these are returned the Message is placed in another HIT
    along with all of the translations recieved and workers are asked to rate the translations
    from best to worst.  The most liked translatio is accepted as the translation."""
    #An AWS account is needed to use Mechanical Turk.  These are the login keys.
    aws_key = models.CharField(max_length=100, null=False)
    aws_secret = models.CharField(max_length=100,null=False)
    #These are the two titles for both phases of the translation.
    title_2nd_phase = models.CharField(max_length=100)
    title_1st_phase = models.CharField(max_length=100)
    #The descriptions
    description_1st_phase = models.CharField(max_length=200)
    description_2nd_phase = models.CharField(max_length=200)
    #Keywords when searching for HITs
    keywords_1st_phase = models.CharField(max_length = 200)
    keywords_2nd_phase = models.CharField(max_length = 200)
    #A chunk of HTML which describes the instructions.
    overview_1st_phase = models.TextField()
    overview_2nd_phase = models.TextField()
    #The rewards offered for both phases of the HIT
    reward_1st_phase = models.CharField(max_length=20,default="0.25")
    reward_2nd_phase = models.CharField(max_length=20,default="0.25")
    #The number of workers that will asked to perform each HIT 
    assignment_count_1st_phase = models.CharField(max_length=20, default="5")
    assignment_count_2nd_phase = models.CharField(max_length=20, default="5")
    #The number of messages to bundle together for the first phase.
    message_count = models.CharField(max_length=20, default="5")
    #Only one configuration can be current at a time.  
    current = models.BooleanField(null=False, default=False)
    #If true the HIT is sent to the developers sandbox.
    sandbox = models.BooleanField(null=False, default=False)

    @classmethod 
    def make_current(modelBase, config):
        """Make a configuration the current one."""
        for m in MTurkConfig.objects.all():
            m.current = False
            m.save()
        config.current = True

	

    def __unicode__(self):
        return self.title

    class Meta:
        db_table = u'configuration'

class ConfigForm(ModelForm):
    class Meta:
        model = MTurkConfig
        #exclude['']

class MTurkTranslation(models.Model):
    """This model is used during while messages are being translated.  It can be deleted
    after the translation is complete but it also holds stats on the translation; cost,
    time, etc.  This is all done in a model rather than an object since time between phases
    could be days."""
    #ID of Translation model.
    translation_id = models.PositiveIntegerField(blank=False,null=False)
    #ID of the configuration used for translation.
    configuration = models.PositiveIntegerField(blank=False,null=False)
    #This is a list of all translations used in the first phase.
    intermediary_translations = models.CharField(max_length=2000,null=True,default=None)
    #The accepted translation.
    translation = models.CharField(max_length=1000,null=True,default=None)
    #HIT id for the first phase.
    HIT_id_1st_phase = models.CharField(max_length=64,default='')
    #HIT id for the second phase.
    HIT_id_2nd_phase = models.CharField(max_length=64)
    #Whether or the HIT is 2 Phase.
    two_phase = models.BooleanField(null=False,default=True)
    #Whether the HIT is currently in Second Phase.
    second_phase = models.BooleanField(null=False,default=False)
    #True when entire process is complete
    complete = models.BooleanField(null=False, default=False)
    #Cost, start time and end time for transation.
    cost = models.CharField(max_length=20, default="0.0")
    start_time = models.DateTimeField(blank=False,default=datetime.now)
    end_time = models.DateTimeField(null=True)
    #For the first phase master is the translation used to reference entire HIT
    master = models.BooleanField(null=False,default=False)
 
    def set_best_translation(self):
        """Count the various rankings given to each translation and accept the lowest."""
        if self.complete:
            i_t = eval(self.intermediary_translations)
            tmp = i_t[0]
            for t in range(1,len(i_t)):
                if i_t[t]['count'] < tmp['count']:
                    tmp = i_t[t]
            self.translation = tmp['value']
            self.save()
            message = Translation.objects.get(id=self.translation_id)
            message.translation = self.translation
            message.save()

    def get_cost(self):
        """Return cost of translations."""
        return self.cost
    
    def is_complete(self):
        """True if translation is complete"""
        return self.complete

    def get_time(self):
        """Return difference between start and end times in seconds."""
        tmp_diff = self.end_time - self.start_time
        return tmp_diff.seconds

class MTurkManager():
    """Manager class for Mechanical Turk Translations.  Handles sending and recieving
    of HITs and tracks them through both phases."""
    
    def __init__(self,hit_check_max,debug=None,router=None):
        """Init for MTurkManager.  Debug is a reference to a debug output, reply 
        determines whether to send translation back to original sender."""
        self.hit_check_max = hit_check_max
        self.debug = debug
        if router:
            self.router = router
            self.reply = True

    def new_message(self,msg_id):
        """When a new message comes in create a new model and set the ID of the translation.
        Then check to see whether there are enough messages to initiate a phase 1 HIT."""
        if self.debug:
            self.debug("MTurkManager: Received new message.")
        config = MTurkConfig.objects.filter(current=True)[0]
        new_translation = MTurkTranslation()
        new_translation.translation_id = msg_id
        new_translation.configuration = config.id
        new_translation.save()
        config = MTurkConfig.objects.get(current=True)
        message_count = int(config.message_count)
        unsent_translations = MTurkTranslation.objects.filter(HIT_id_1st_phase = '')[:message_count]
        if self.debug:
            self.debug("MTurkManager: Have %d of %d untranslated messages",
                       len(unsent_translations),message_count)
        if len(unsent_translations) >= message_count:
            if self.debug:
                self.debug("MTurkManager: Initiating new HIT.")
            ret = self.send_HIT(1,config,translations=unsent_translations)
            set_master = False
            for u in unsent_translations:
                u.HIT_id_1st_phase = ret
                if not set_master:
                    u.master = True
                    set_master = True
                u.save()
        else:
            if self.debug:
                self.debug("MTurkManager:  Need %d more messages for HIT.",
                           (message_count - len(unsent_translations)))

    def check_submissions(self):
        """Check incomplete HITs.  Will only check a certain number per call, controlled
        by self.hit_check_max."""
        hits_checked = 0
        if self.debug:
            self.debug("MTurkManager: Looking for translations.")
        #First try to gather HITs in phase 2.
        hits = MTurkTranslation.objects.filter(two_phase=True,second_phase=True,complete=False)[:self.hit_check_max]
        if hits:
            if self.debug:
                self.debug("MTurkManager: checking phase 2 submissions.")
            for h in hits:
                if len(h.HIT_id_2nd_phase) > 0:
                    config = MTurkConfig.objects.get(id=h.configuration)
                    ret = self.check_HIT(h.HIT_id_2nd_phase,2,config)
                    if ret:
                        self.process_hit_return(ret,h)
                    hits_checked += 1
        #Use remain time to check phase 1 HITs
        if hits_checked < self.hit_check_max:
            hits = MTurkTranslation.objects.filter(second_phase=False,complete=False,master=True)[:(self.hit_check_max - hits_checked)]
            if hits:
                if self.debug:
                    self.debug("MTurkManager: checking phase 1 submissions.")
                for h in hits:
                    config = MTurkConfig.objects.get(id=h.configuration)
                    ret = self.check_HIT(h.HIT_id_1st_phase,1,config)
                    if ret:
                        if self.debug:
                            self.debug("MTurkManager: sending to process_hit_return.")
                        self.process_hit_return(ret,h)
                                                                                   
    def process_hit_return(self,ret,hit):
        """Called when a HIT has been returned.  Parses the returned data and determines
        what to do based on the current phase of the HIT."""
        if self.debug:
            self.debug("MTurkManager: processing HIT returns.")
        if hit.second_phase:
            translations = eval(hit.intermediary_translations)
            for k in ret.keys():
                count = 0
                for a in ret[k]:
                    count += int(a)
                for t in translations:
                    if t['id'] == k:
                        t['count'] = count
            hit.intermediary_translations = repr(translations)
            hit.end_time = datetime.now()
            hit.complete = True
            curr_cost = float(hit.cost)
            config = MTurkConfig.objects.get(id=hit.configuration)
            curr_cost += (float(config.reward_2nd_phase)*float(config.assignment_count_2nd_phase))
            hit.cost = str(curr_cost)
            hit.save()
            hit.set_best_translation()
            hit.save()
            if self.debug:
                self.debug("MTurkManager: Saved new translation.")
            if self.reply:
                message = Translation.objects.get(id=hit.translation_id)
                if message.has_been_translated:
                    outgoing = "Your translation: " + message.translation
                    backend = self.router.get_backend('pygsm')
                    if self.debug:
                        self.debug("MTurkManager: Sending %s to original sender - %s.",outgoing,message.phone_number)
                    backend.message(message.phone_number,outgoing).send()
                    #backend.message(message.phone_number,outgoing).send()
        else:
            if self.debug:
                self.debug("MTurkManager: making intermediary translations.")
            for k in ret.keys():
                translation_list = []
                index = ord('A')
                for t in ret[k]:
                    tmp_str = k + '-' + chr(index)
                    index += 1
                    translation_list.append({'id':tmp_str,
                                             'value':t,
                                             'count':None})
                h = MTurkTranslation.objects.get(id=k)
                h.intermediary_translations = repr(translation_list)
                config = MTurkConfig.objects.get(id=h.configuration)
                cost_per_message = float(config.reward_1st_phase)/len(ret) * float( 
                    config.assignment_count_1st_phase)
                curr_cost = float(h.cost) 
                h.cost = str(curr_cost + cost_per_message)
                h.second_phase = True
                h.save()
                self.make_second_HIT(h)

    def make_second_HIT(self,h):
        config = MTurkConfig.objects.get(id=h.configuration)
        translations = eval(h.intermediary_translations)
        if self.debug:
            self.debug("MTurkManager: %s",translations)
        question_list = []
        for t in translations:
            tmp = (t['value'],t['id'])
            question_list.append(tmp)
            if self.debug:
                self.debug("MTurkManager: %s",repr(question_list))
        ret = self.send_HIT(2,config,question_list=question_list)
        if ret != -1:
            h.HIT_id_2nd_phase=ret
            h.save()

    def send_HIT(self,phase,config,translations = None, question_list = None):
        """Send a new HIT based on the current phase."""
        config = MTurkConfig.objects.get(current=True)
        #If question_list in None it is a new HIT and questions come from self.hit_list
        if question_list == None:
            #Generate a new question list based on new translations.
            question_list = []
            for t in translations:
                #Each question consists of the message and the MTurkTranslation id as
                #an identifier.
                tmp_message = Translation.objects.get(id=t.translation_id)
                question_list.append((tmp_message.original_message,t.id))
        #I'm not sure what the options are for, but we can't send a hit without them
        options = [("This is an option","option_id")]
        #Set HIT options based on phase.
        if phase == 1:
            assignment_count = config.assignment_count_1st_phase
            overview = config.overview_1st_phase
            title = config.title_1st_phase
            description = config.description_1st_phase
            keywords = config.keywords_1st_phase
            reward = config.reward_1st_phase
            is_numeral = False
        else:
            id = question_list[0][1].split('-')[0]
            msg = Translation.objects.get(id=id)
            question_for_ranking = "<p>%s</p>" % (msg.original_message)
            assignment_count = config.assignment_count_2nd_phase
            overview = config.overview_2nd_phase + question_for_ranking
            title = config.title_2nd_phase
            description = config.description_2nd_phase
            keywords = config.keywords_2nd_phase
            reward = config.reward_2nd_phase
            is_numeral = True
        #cast aws_key and aws_secret from unicode to string
        #hmac module will fail otherwise
        aws_key = str(config.aws_key)
        aws_secret = str(config.aws_secret)
        hitter = textonic.HITGenerator(question_list = question_list,
                                       assignment_count = assignment_count,
                                       overview_content = overview,
                                       answer_options = options,
                                       title = title,
                                       description = description,
                                       keywords = keywords,
                                       reward = reward,
                                       AWS_KEY = aws_key,
                                       AWS_SECRET = aws_secret,
                                       is_numeral = is_numeral,
                                       )
        sandbox = 'false'
        if config.sandbox:
            sandbox = 'true'
        ret = hitter.SubmitHIT(sandbox=sandbox)
        if(ret):
            if self.debug:
                self.debug("MTurkManager: new phase 2 HIT - %s",ret[0].HITId)
            return ret[0].HITId
        else:
            #HIT send failed
            if self.debug:
                self.debug("MTurkManager: Failed to post new HIT.")
            return -1

    def check_HIT(self,hit_id,phase,config):
        """Check to see if a HIT has been completed."""
        if self.debug:
            self.debug("MTurkManager: checking HIT - %s",hit_id)
        if phase == 1:
            assignment_count = config.assignment_count_1st_phase
        else:
            assignment_count = config.assignment_count_2nd_phase
        sandbox = 'false'
        if config.sandbox:
            sandbox = 'true'
        aws_key = str(config.aws_key)
        aws_secret = str(config.aws_secret)
        hit_ret = textonic.HITRetriever(aws_key,aws_secret,hit_id)
        ret = hit_ret.RetrieveHIT(sandbox = sandbox)
        hitsers = {}
        if len(ret) == int(assignment_count):
            for ans in ret:
                for form in ans.answers[0]:
                    answer = ''
                    if phase == 2:
                        answer = form.SelectionIdentifier
                    else:
                        answer = form.FreeText
                    added = False
                    question_id  = form.QuestionIdentifier
                    for k in hitsers.keys():
                        if k == question_id:
                            hitsers[k].append(answer)
                            added = True
                    if not added:
                        hitsers[question_id] = [answer]
        else:
            if self.debug:
                self.debug("MTurkConfig: HIT not complete.")
        return hitsers
                    
            
            
