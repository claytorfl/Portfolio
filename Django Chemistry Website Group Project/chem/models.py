from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from random import *
from .utility import *
from re import *
from statistics import *


#Contains parameters used to determine what score a student should get after answering a question correctly
class ScoreAlgorithm(models.Model):
    name = models.CharField(max_length=200)
    per_day_penalty_percent = models.FloatField(default=0)
    max_day_penalty = models.FloatField(default=0)
    per_wrong_answer_penalty_percent = models.FloatField(default=0)
    max_wrong_answer_penalty = models.FloatField(default=0)

    def __str__(self):
        return self.name

    #Scores the question using the given penalty parameters
    #The parameters are the max possible score, the number of tries, and the number of days since
    #the question began
    def student_score_algorithm(self, max_score, tries, time_taken):

        #Determines what percentage to take off for the number of days late the answer is
        time_penalty = time_taken*self.per_day_penalty_percent

        #If the time penalty is above the maximum time penalty set it to the maximum
        if time_penalty > self.max_day_penalty:
            time_penalty = self.max_day_penalty

        #Determines what percentage to take off for the numbers of wrong answers to a question
        wrong_penalty = (tries-1)*self.per_wrong_answer_penalty_percent

        #If the wrong answer penalty is above the max then it is set to the maximum penalty
        if wrong_penalty > self.max_wrong_answer_penalty:
            wrong_penalty = self.max_wrong_answer_penalty

        #Determines the score awarded by taking the max score and subtracting the penalty points
        return max_score - max_score * ((time_penalty+wrong_penalty)/100)

# Contains bank entries, which each have  question, a start time, and an end time
#A list of questions for teams to answer over a time period
class QuestionBank(models.Model):
    '''The Question Bank cotains a list of Bank Entries that assign a Question to a start and end time. Each Team is
    assigned a Question Bank'''

    name = models.CharField(max_length=200)
    max_score = models.IntegerField(default=10)
    scorer = models.ForeignKey(ScoreAlgorithm)

    #Used to call a Question bank's scorer to determine what score a student should get after answering a question
    def student_score_algorithm(self, tries, time_taken):
        return self.scorer.student_score_algorithm(self.max_score, tries, time_taken)

    # Run the scor algorithm that gives all teams with this bank a weighted score
    #The QuestionBank model has access to all Teams that are foreign keyed to it
    #It can collect their scores and use them to find the averages and standard deviations
    #necessary to do the socring algorithm to weight the scores
    def team_score_algorithm(self):
        team_dict = {}
        all_team_score_list = []
        #Have all teams find their total and average score
        #Append their scores to an entry in a dictionary, one key for each size of team

        for i in self.team_set.all():
            key = str((i.number//1)*1)
            i.tallyscore()
            all_team_score_list.append(i.score)
            #if str(i.number) in list(team_dict.keys()):
            if str(key) in list(team_dict.keys()):
                team_dict[key].append(i.score)
            else:
                team_dict[key] = [i.score]

        #team_dict is now a dictionary seperating the team's scores into groups based on their size
        #print(team_dict)
        #return True

        if len(all_team_score_list) < 2:
            total_stdev = 0
        else:
            total_stdev = stdev(all_team_score_list)
        total_average = mean(all_team_score_list)
        total_sum = sum(all_team_score_list)

        stdev_dict = {}
        average_dict = {}
        sum_dict = {}
        for i in list(team_dict.keys()):

            if len(team_dict[i]) == 1:
                stdev_dict[i] = 0
            else:
                stdev_dict[i] = stdev(team_dict[i])
            average_dict[i] = mean(team_dict[i])
            sum_dict[i] = sum(team_dict[i])

        print(stdev_dict)
        print(average_dict)
        print(sum_dict)

        for i in self.team_set.all():
            key = str((i.number//1)*1)
            print(i.team_name)
            start_score = i.score
            print(start_score)
            group_average = average_dict[key]
            print(group_average)
            group_std = stdev_dict[key]
            print(group_std)
            if group_std == 0:
                weightedscore = start_score-group_average
            else:
                weightedscore = (start_score-group_average)/group_std
            print(weightedscore)
            print(total_stdev)
            print(total_average)
            weightedscore = weightedscore*total_stdev + total_average
            print(weightedscore)
            i.weightedscore = round(weightedscore, 2)
            print(i.weightedscore)
            #i.weightedscore = round(start_score/total_average)
            #print(weightedscore)
            i.save()



    # Returns the currently used question for this Question Bank
    def current_question(self):
        for i in self.bankentry_set.all():
            if i.is_current():
                return i.question
        return False

    # Returns a current bank entry of the Question Bank based on the time
    def current_entry(self):
        for i in self.bankentry_set.all():
            if i.is_current():
                return i
        return False

    # returns all current entries in the question bank based on the time
    def current_entries(self):
        entrylist = []
        for i in self.bankentry_set.all():
            if i.is_current():
                entrylist.append(i)
        return entrylist

    #Returns a randomly chosen current question
    def get_question(self):
        return self.current_entries()[randint(0, len(self.current_entries())-1)]

    def __str__(self):
        return self.name


# An individual question
class Question(models.Model):
    '''A Question that a Student can answer. Each Student only has 1 current question at a time'''

    # The text that is printed out
    # If the question has parameters but their keys in the question text
    # Like "What is X plus Y"
    question_text = models.CharField(max_length=2000)

    def __str__(self):

        # If the question text is too long only show the first 30 characters
        if len(self.question_text) > 30:
            return self.question_text[:30]
        return self.question_text

    #Returns a question's answer (will always be a subclass of the abstract class answer)
    #A question shouldn't have more than one kind of answer connected to it
    def answer(self):
        if hasattr(self, 'mathanswer'):
            return self.mathanswer
        if hasattr(self, 'balanceanswer'):
            return self.balanceanswer

    #Creates a question log for a student that is viewing this question
    #Encapsulates the question and the new question text and new answer that come from
    #evaluating the randomized parameters
    def make_question_log(self):
        answer = self.answer()
        qlog = QuestionLog()

        #Sets the question logs instance variables
        qlog.question = self
        newtext = self.question_text
        newanswertext = answer.answer_text
        dictstring = ''

        #If the Question has random parameters then the question log's question text, answer text, and
        #dictstring are changed
        if self.parameter_set.all():
            dictlist = []

            #Iterates through the Question's parameters to determine what random value to replace
            for i in self.parameter_set.all():
                dictlist.append(i.key)
                dictlist.append(str(i.evaluate()))
                newtext = keyreplace(newtext, dictlist[-2], dictlist[-1])
                newanswertext = keyreplace(newanswertext, dictlist[-2], dictlist[-1])
            dictstring = ':'.join(dictlist)
        qlog.dictstring = dictstring
        qlog.new_text = newtext
        qlog.new_answer = newanswertext

        #If a balance question is being created replace all of the numbers in the question text
        #with numbers surrounded by the sub tags so they are subscripts
        if hasattr(self, 'balanceanswer'):
            p = compile('(?P<name>\d)')
            qlog.new_text = p.sub('<sub>\g<name></sub>', qlog.new_text)
        #qlog.save()
        return qlog



    #Generates a random version of the question with it's parameters filled in
    #So {X}+{Y} would become 1+4, the parameters are filled in using the Question's parameter_set
    def generate_question(self):
        newtext = self.question_text
        newanswer = self.answer().answer_text
        for i in self.parameter_set.all():
            newvalue = i.evaluate()
            newtext = keyreplace(newtext, i.key, str(newvalue))
            newanswer = keyreplace(newanswer, i.key, newvalue)
        newq = Question()
        newq.question_text = newtext

        #If a question has a Balance Answer then it must be a question about balancing chemical equations
        #So each number in it's question text is given subscript html tags
        if hasattr(self, 'balanceanswer'):
            p = compile('(?P<name>\d)')
            newq.question_text = p.sub('<sub>\g<name></sub>', newq.question_text)
        newq.answer = self.answer().clone()
        newq.answer.answer_text = newanswer
        return newq

    #Generates a nonrandom version of the question using a given dictstring
    #If a student has already seen a question it shouldn't rerandomize so this function
    #is used to make sure they see the same one each time
    def generate_specific_question(self, dictstring):
        dictlist = dictstring.split(":")
        qtext = self.question_text
        atext = self.answer().answer_text
        newq = Question()
        for i in self.parameter_set.all():
            qtext = keyreplace(qtext, i.key, dictlist[dictlist.index(i.key)+1])
            atext = keyreplace(atext, i.key, dictlist[dictlist.index(i.key)+1])
        newq.question_text = qtext

        #If a question has a Balance Answer then it must be a question about balancing chemical equations
        #So each number in it's question text is given subscript html tags
        if hasattr(self, 'balanceanswer'):
            p = compile('(?P<name>\d)')
            newq.question_text = p.sub('<sub>\g<name></sub>', newq.question_text)
        newq.answer = self.answer
        newq.answer().answer_text = atext
        return newq


#Abstract class for the answer to a question
class Answer(models.Model):
    '''Abstract class for the Answer to a Question. Each Answer has a One to One relationship with a Question'''
    answer_text = models.CharField(max_length=200)
    question = models.OneToOneField(Question)

    #Prints out the answer in the proper form (with units or other additions)
    def print_answer(self, postdict):
        return self.answer_text

    #Returns the computed answer as a string (unsure if necessary, may be edited out)
    def evaluate(self):
        return self.answer_text

    #Creates a copy of the Answer object
    def clone(self):
        return False

    #Returns true is answer is correct using the POST dictionary given to the GradeView
    def is_correct(self, postdict):
        return self.is_correct_specific(postdict, self.answer_text)

    def is_correct_specific(self, postdict, given_answer):
        return False

    def get_type(self):
        return 'abstract'

    def get_html(self, text):
        return 'Answer'

    def is_empty(self, postdict):
        return False

    def __str__(self):
        return self.answer_text

    class Meta:
        abstract = True


#Answer used for mathemical questions with units
class MathAnswer(Answer):
    '''Answer Model used when a Question involves mathematical calculations or units'''
    percent_error = models.FloatField(default=0)
    additive_error = models.FloatField(default=0)
    answer_unit_text = models.CharField(max_length=20, null=True, blank=True)
    rounding = models.IntegerField(default=0)

    def get_type(self):
        return 'math'

    #Returns the answer as a string witha single number
    def print_answer(self, postdict):
        print(postdict['question'])
        print(postdict['unit'])
        print(self.rounding)
        return str(round(eval(str(postdict['question']))*eval(postdict['unit']))) + self.answer_unit_text

    #Returns a string version of the evaluated answer
    def evaluate(self):
        return str(round(eval(self.answer_text), self.rounding))

    #Returns a new MathAnswer object with the same instance variable values as the old MathAnswer
    #Used to duplicate MathAnswer without messing up the One to One relatioship with Question
    def clone(self):
        newanswer = MathAnswer()
        newanswer.answer_text = self.answer_text
        newanswer.additive_error = self.additive_error
        newanswer.percent_error = self.percent_error
        newanswer.answer_unit_text = self.answer_unit_text
        newanswer.rounding = self.rounding
        return newanswer


    #Calculates if a user's answer (in POST dictionary form) is correct
    #is_correct_specific is different from is_correct because instead of using Answer's answer_text it uses
    #the give_answer parameter to compare the post dictionary to
    def is_correct_specific(self, postdict, given_answer):

        #Multiplies the student's answer by the chosen unit's normalizer so it has the same units as the
        #answer the administrator assigned to the question
        answer = round(eval(postdict['question'])*eval(postdict['unit']), self.rounding)
        print(given_answer)
        given_answer = round(eval(given_answer), self.rounding)
        percenterror = abs((given_answer-answer))/given_answer*100
        additiveerror = abs(given_answer-answer)
        trueanswer = given_answer
        print(answer, trueanswer)

        #If an max additive error is specificied it checks it
        #If a max percent error is specified it checks it
        #If neiteher a additive or percent error is used it checks if the true answer and user answer are equal
        #Or if the additive error is less than the smallest floating point number
        #If one of the conditions is true then the answer is correct
        if (additiveerror<self.additive_error and self.additive_error!=0) or (percenterror<self.percent_error and self.percent_error!=0) or trueanswer==answer or additiveerror<2.2250738585072014**-307:
            return True
        else:
            return False

    #Returns a string of the html to display for the input form for a math question
    #The question text is displayed normally
    #And there is a single input box and a possible unit dropdown menu added
    def get_html(self, text):
        html = '<h1>' + text + '</h1><input type="text" name="question" id="question"/>'

        #If this answer has units then create the dropdown menu, otherwise add an invisible text input
        #field that has id unit and value of 1, since that will have no effect on the answer and units
        #are needed for the MathAnswer's is_correct method
        if self.question.unitdropdown_set.all():
            html += '<select name="unit">'
            for i in self.question.unitdropdown_set.all():
                html += '<option value=' + str(i.normalizer) + '>' + i.text + '</option>'
            html += '</select>'
        else:
            html += '<input type="text" name="unit" value="1" hidden/>'

        return html

    #Returns true if the user failed to type in one of the answer input boxes
    def is_empty(self, postdict):
        if postdict['question']=='':
            return True
        return False


    def __str__(self):
        return self.answer_text + self.answer_unit_text




#Answer used for problems involving balancing chemical equations
class BalanceAnswer(Answer):
    '''Answer Model that is used when a Question involves balancing a chemical equation'''

    def get_type(self):
        return 'balance'

    #Creates a new instance of BalanceAnswer with the same fields as this BalanceAnswer
    def clone(self):
        newanswer = BalanceAnswer()
        newanswer.answer_text = self.answer_text
        return newanswer

    #Takes a Post dictionary and a given answer and returns true if the Post dictionary contains the
    #correct answer when the correct answer is given answer
    def is_correct_specific(self, postdict, given_answer):
        answer_list = given_answer.split()
        for i in range(len(answer_list)):
            #print( postdict[str(i+1)], answer_list[i])
            if postdict[str(i+1)] != answer_list[i]:
                return False
        return True

    #Returns a string of the html for the input form to answer a balance question
    #The question string has input boxes put in places of the brackets []
    #The user fills in one box for each coefficient in the chemical equation
    def get_html(self, text):

        #Splits the text by []'s so the []'s can be replaced by the html for text input boxes
        balancelist = text.split('[]')[1:]
        html = ''
        for i in range(len(balancelist)):
            html += '<input type="text" maxlength="2" size="2" name="' + str(i+1) + '" id="' + str(i+1) + '"/><strong>' +balancelist[i] + '</strong>'
        return html

    #Returns True if the user failed to type something in one of the answer input boxes
    def is_empty(self, postdict):
        if postdict['1']=='' or postdict['2']=='' or postdict['3']=='' or postdict['4']=='':
            return True
        return False


#Replaces a key in the question and answer strings of the question with the evaluated output of the value
#The key is some characters inside curly braces: {X}, {mass}, {variable}
#The value is python code that is evaluated to get a number
class Parameter(models.Model):
    '''A Parameter represents one of the randomized variables of a Question'''

    #A single character that to be replaced in the questin text and answer
    key = models.CharField(max_length=200)

    #Python code to be evaluated to find the value that will replaced the key character
    #in the question text and answer
    #If left blank then low, high, and round are used instead to generate a random number
    value = models.CharField(max_length=200, blank=True, null=True)

    #The question the parameter belongs to
    question = models.ForeignKey(Question)


    #If the value field is left blank then the Parameter will use low, high, and round to
    #find a random value between low and high rounded to round decimal points
    #The lowest random number that can be chosen
    low = models.FloatField(default=0)

    #The highest random number that can be chosen
    high = models.FloatField(default=0)

    #How many decimal places the random number is rounded to
    round = models.IntegerField(default=0)


    #Evalutes the random parameter and returns a specific value
    #Evaluates the code into the value variable of the parameter
    #If the value box is blank then a simple method using low and high is used
    def evaluate(self):

        #If the Parameter's value field has something in it then evaluate it like it is python code to
        #find the random value for this Parameter
        if self.value:
            return eval(self.value)

        #If the Parameter's value field is blank then use low, high, and round to generate a random number
        #within a specific range with a specific precision
        else:
            return round(random()*(self.high-self.low) + self.low, self.round)

    def __str__(self):
        return self.key + ':' + str(self.question)

#Model that is used to add options to the units drop down menu the student can use when answering a question
class UnitDropDown(models.Model):
    '''Model that represents a unit and a number that converts the unit to the unit for the Question's answer'''

    #The text of the option added to the drop down menu
    text = models.CharField(max_length=200)

    #The question that this drop down item is associated with
    question = models.ForeignKey(Question)

    #A number that will be multiplied with the student's answer to convert it to the units of the answer key answer
    #So if the answer key answer is in meters and the student selects centimeters from the drop down
    #Their answer will be multiplied by 0.01 to convert it to meters so it can be compared to the answer key answer
    normalizer = models.FloatField(default=1)

    def __str__(self):
        return self.text




#A single entry in the QuestionBank
#Allows questions to be put into a list with dates and times
class BankEntry(models.Model):
    '''Each Question Bank has many Bank Entries. A Bank Entry is used to assign a Question to a
    Start Time and End Time'''

    #The question that will be used for the QuestionBank when the current time is between start time and end time
    question = models.ForeignKey(Question)

    #The time the question will first appear on the web page
    starttime = models.DateTimeField()

    #The time the question will no longer be able to be answered and will stop being current
    endtime = models.DateTimeField()

    #The question bank the Bank Entry belongs to
    bank = models.ForeignKey(QuestionBank)

    #Returns true if the Bank Entry is current and its question should be used this week
    def is_current(self):
        return timezone.now()>self.starttime and timezone.now()<self.endtime

    def __str__(self):
        return str(self.question) + ':' + self.bank.name


#School, students and teachers connect to it with foreign keys
class School(models.Model):
    '''Students and Teacher's can form a ForeignKey connection to a School'''
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


#Groups together students and teachers into teams/classes for leaderboard and organizational purposes
class Team(models.Model):
    '''A Team has Students and Teachers and assigns them to a Question Bank
    The Team Model is used to organize users for scoring and grouping puruposes'''
    team_name = models.CharField(max_length=200)

    #The number of students in the team (calculated with tallyscore function)
    number = models.IntegerField(default=0)

    #The average score of all students in the team
    score = models.FloatField(default=0)

    #The average current week score of all students in the team
    weekscore = models.FloatField(default=0)

    #The scores all of the team's students added togetheer
    totalscore = models.FloatField(default=0)

    #The average score of all students in the team
    averagescore = models.FloatField(default=0)

    #The score of the team after using a weighted algorithm (score_algorithm in the team's Question Bank)
    weightedscore = models.FloatField(default=0)

    #The average, total, and weighted version of the team's weekscore
    averageweekscore = models.FloatField(default=0)
    totalweekscore = models.FloatField(default=0)
    weightedweekscore = models.FloatField(default=0)

    #The Question Bank that the team gets its questions from
    bank = models.ForeignKey(QuestionBank)

    #Determines the average score for the team of students total and for the current week
    #also computes a few other kinds of scores that could be used in various scoring algorithms
    def tallyscore(self):
        score = 0
        weekscore = 0
        number = len(self.student_set.all())
        if number==0:
            self.score = 0
            self.weekscore = 0
            self.averageweekscore = 0
            self.totalweekscore = 0
            self.weightedscore = 0
            self.weightedweekscore = 0
            self.number = 0
            self.averagescore = 0
            self.totalscore = 0
            self.save()
            return 0
        for i in self.student_set.all():
            score += i.score
            if not(i.still_current()):
                i.weekscore = 0
            weekscore += i.weekscore
        self.score = round(score/number, 2)
        self.averagescore = score/number
        self.totalscore = score
        self.weekscore = round(weekscore/number, 2)
        self.averageweekscore = weekscore/number
        self.totalweekscore = weekscore
        self.weightedweekscore = weekscore
        self.weightedscore = round(score/number, 2)

        self.number = number
        self.save()

        #Calls the Question Bank's team score algorithm, which runs an algorithm
        #that weights team scores based on team size, average score, and standard deviation
        #Currently broken,
        #self.bank.team_score_algorithm()

    def __str__(self):
        return self.team_name


#Class assigned to users who are students
#Stores their score, team, and methods to get question logs for their current question
#and the chekc answeres, add to their score
class Student(models.Model):
    '''Has a OneToOne connection with a User
    Belongs to 1 team, has 1 school
    A student gets its current question from its Team's Question Bank'''
    user = models.OneToOneField(User)

    #The student's total score
    score = models.IntegerField(default=0)

    #The score the student received for this week's question (0 if they haven't answered yet)
    weekscore = models.IntegerField(default=0)

    #The school the student goes to
    school = models.ForeignKey(School)

    #The team/class the student belogns to
    team = models.ForeignKey(Team)

    #True if the student is using a default password
    #When they first log in they will be prompted to change it
    defaultPass = models.BooleanField(default=False)


    #Returns the question log for the student's current question
    #If there is no current question then False is returned
    def get_questionlog(self):

        #If there are no question logs or the last question log used isn't current make a new one
        #Otherwise use the last one
        if len(self.questionlog_set.all()) == 0 or not(self.still_current()):
                #If a new question must be acquired then it must be a new week and the student's
                #weekscore can be set back to 0
                self.weekscore = 0
                self.save()

                #If the student's Question Bank has any current questions then pick a random one
                #and make that their new question
                if self.team.bank.current_entries():

                    #The steps to make a new question log

                    #Finds a random current question
                    entry = self.team.bank.current_entries()[randint(0, len(self.team.bank.current_entries())-1)]
                    q = entry.question

                    #Uses the question to generate a question log for that question
                    qlog = q.make_question_log()

                    #The question log is foreign keyed to the Student
                    qlog.student = self

                    #The question log keeps track of the questions start and end times
                    qlog.start_time = entry.starttime
                    qlog.end_time = entry.endtime
                    qlog.save()
                    return qlog
                else:

                    #If false is returned then there is no current question to create a question log from
                    #So there is no current question at that time
                    return False
        else:

            #If the student has a current question log then return that current question log
            #(the one with the latest start time)
            return list(self.questionlog_set.all().order_by('start_time'))[-1]

    #Returns True if the student's latest question log represents a current question or if it is past
    #its end time
    def still_current(self):
        if list(self.questionlog_set.all()):

            #Finds the most current question log a student has and checks if it is current
            return list(self.questionlog_set.all().order_by('start_time'))[-1].is_current()

        #If the user has no question log then return False because they can't have a current question log
        else:
            return False

    #Checks the answer stored in the POST dictionary postdict
    def check_answer(self, postdict):
        return self.get_questionlog().question.answer().is_correct_specific(postdict, self.get_questionlog().new_answer)

    #Function that runs and can use the parameters of the Student object to determine their score for a completed question
    def student_score_algorithm(self):

        #Calls the student's current question log's scoring algorithm
        #Since the question log knows how long it has been since the question started and how many
        #tries the student took to answer correctly
        score = self.get_questionlog().student_score_algorithm()

        #Their score becomes the student's score for the current week
        self.weekscore = score

        #Adds the new score to the student's total score variable
        self.score += score

        #saves the student's state
        self.save()
        return score

    def get_current_entry(self):

        return self.team.bank.current_entries()[self.question_number]


    def __str__(self):
        return self.user.username


#Class assigned to users who are teachers
class Teacher(models.Model):
    '''Has a OneToOne connection with a User
    Has a school and can have multiple teams of students'''

    user = models.OneToOneField(User)

    #The school the teacher is at
    school = models.ForeignKey(School)

    #The teams/classes the teacher teaches
    team = models.ManyToManyField(Team)

    #Generates the example questions the teacher sees
    #Looks through the teams the teacher is a part of and makes a list of all current questions
    #Then for each current question an example question is created with q.generate_question and
    #appended to a list
    def generate_question(self):
        qlist = []
        banklist = []

        #Creates a list of all of the question banks that are connected to the teams a teacher is part of
        for t in self.team.all():
            if t.bank not in banklist:
                banklist.append(t.bank)

        #Adds an example question for each current question of the Question Banks in banklist
        for k in banklist:
            for i in k.current_entries():
                qlist.append(i.question)\

        #The list that will contain the example questions
        newqlist = []

        #Appends a generated example question to newqlist so the teacher has an example for each question
        for q in qlist:
            newqlist.append(q.generate_question())
        return newqlist

    def __str__(self):
        return self.user.username

#Keeps track of each answer a student submits for each question so teachers can review it later
#Doesn't have any important functions, just stores data in a convenient spot foreign keyed to a
#specific student
class AnswerLog(models.Model):
    '''Model that contains data about each time a Student answered a Question'''

    #The student this log is assigned to
    student = models.ForeignKey(Student)

    #The text of the question the answer was for
    question_text = models.CharField(max_length=200)

    #The answer the student submitted
    student_answer = models.CharField(max_length=200)

    #The actual answer of the question
    actual_answer = models.CharField(max_length=200)

    #The start time of the question this answer is for
    question_start_time = models.DateTimeField(default=timezone.now)

    #What time the student submitted this specific answer
    answer_time = models.DateTimeField(default=timezone.now)

    #The question bank the question belongs to
    bank = models.ForeignKey(QuestionBank)

    #If the answer the student submitted was correct or not
    correct = models.IntegerField(default=0)

    def __str__(self):
        return self.student.user.username + ':' + str(self.answer_time)

#Model that keeps track of each question the student is assigned, what random values they give the parameters, and what
#their final answer is
#Question logs allow the Student model to determine if it has a current question and what question it is
#currently working on
#The question log allows a randomized question to be saved without requiring a new Question to be generated
#every time the student needs to intereact with a specific question
class QuestionLog(models.Model):
    '''Contains data used to give each user a randomized question and keeps track of data about how the student
answers the question'''

    #The student the question log is assigned to
    student = models.ForeignKey(Student)

    #The question the log is linked to
    question = models.ForeignKey(Question)

    #The question text with randomized parameters filled in
    #What the student sees
    new_text = models.CharField(max_length=2000)

    #The answer with randomized parameters filled in
    new_answer = models.CharField(max_length=2000, default='answer')

    #A string that is like a dictionary and contains the ranodm variables picked for the parameters
    #Could be useful if a question's text or answer text is changed and the values of the random values
    #are needed to reevaluate things
    #Currently isn't used for anything
    dictstring = models.CharField(max_length=200)

    #A string of the POST request dictionary submitted the last time the student answered the question
    current_answer = models.CharField(max_length=2000, default='')

    #The currently submitted answer, but instead of a dictionary it is formatted more legibly by the
    #answer's print_answer method
    current_answer_print = models.CharField(max_length=2000, default='')

    #The start time of the question fo this log
    start_time = models.DateTimeField(default=timezone.now)

    #The end time of the question for this log
    end_time = models.DateTimeField(default=timezone.now)

    #Boolean that says if the student has correct answered this question yet
    correct = models.BooleanField(default=False)

    #How many tries the student has used to answer the question
    tries = models.IntegerField(default=0)

    #The score the student is given after correctly answering the question
    given_score = models.IntegerField(default=0)


    #Returns True or False based on if the answer in the postdict dictionary is correct
    def check_answer(self, postdict):

        #Saves the current post dictionary to this log so it can be looked at later by teacher's or administrators
        self.current_answer = str(postdict)
        self.save()

        #Calls is_correct_specific, which takes an answer object, and gives it an answer dictionary and
        #the actual correct answer and it checks if the two are equal
        return self.question.answer().is_correct_specific(postdict, self.new_answer)

    def __str__(self):
        return self.student.user.username + ':' + str(self.question)

    #Returns True is the question is current
    def is_current(self):
        return timezone.now()>self.start_time and timezone.now()<self.end_time

    #The question returns a score based on the time and number of tries a student took to answer a question
    def student_score_algorithm(self):

        #A timezone date - a timezone date equals a datetime delta with an attribute days
        #The arguments for the bank's student score algorithm are the number of tries and the number of days since
        #the question started
        #Calls the student's Question Bank's scoring algorithm to determine what points to award the student
        #for answering the question correctly
        self.given_score = self.student.team.bank.student_score_algorithm(self.tries, (timezone.now()-self.start_time).days)
        self.save()
        return self.given_score