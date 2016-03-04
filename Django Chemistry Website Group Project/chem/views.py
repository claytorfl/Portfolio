from random import *
from .utility import *
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.models import User
from .models import *
from re import *

#What is seen when the user first logs in
class MainMenuView(View):

    def dispatch(self,request):

        #If the user is a student check if they have a default password
        if hasattr(request.user, 'student'):

            #If the student has a default password take them to the change password page and request
            #that they change it to something else
            if request.user.student.defaultPass:
                return HttpResponseRedirect(reverse("chem:changePass"))

        #If the user doesn't have an email then reqeust that they enter one
        #The email is necessary for helping a user replace a Forgotten Password
        if not request.user.email:
            return HttpResponseRedirect(reverse("chem:changeEmail"))

        #If a user is a student then either display the current question for them or say that there
        #is no question
        if hasattr(request.user, 'student'):

            #Get the most current question log for the student
            #The question log has a reference to the current question, the question text, the answer text
            #and the start and end time of the question
            qlog = request.user.student.get_questionlog()

            actualquestion = qlog.question.generate_specific_question(qlog.dictstring)
            #If a question log is found the question will display on the main page
            return render(request, 'chem/index.html', {
                'user': request.user,
                'newquestion': qlog,

                #Boolean that indicates if the student already answered the question correctly
                'correct': qlog.correct,

                #Debug text, prints out the answer so it can be answered quickly for demos
                #'answer': actualquestion.answer().evaluate(),#qlog.question.answer().print_answer({'question': qlog.new_answer, 'unit': '1'}),

                #The html that creates the answer forms for the question
                'html': qlog.question.answer().get_html(qlog.new_text)
            })
        #If the user is a teacher then generate a list of all possible questions their students could be looking at
        if hasattr(request.user, 'teacher'):

            #The teacher's generate question function returns a list of example questions
            #for all of teams the teacher is currently a part of
            question_list = request.user.teacher.generate_question()


            return render(request, 'chem/index.html', {
                'user': request.user,
                'newquestion': question_list,
            })

        #If the user is staff (an admin) then return this render
        if request.user.is_staff:
            return render(request, 'chem/index.html', {
                'user': request.user,
            })




#The view the user sees before they login
class LoginView(generic.ListView):
    model = Question
    def dispatch(self, request):
        return render(request, 'chem/login.html')

#Logs the user out and takes them back to the login page
class LogOutView(View):
    def dispatch(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('chem:login'))

#View that displays a list of links to all leaderboards (will be edited to go to a template with tabs that show each leaderboard on the same webpage)
class LeaderboardView(View):

    def dispatch(self, request):
        studentteamlist = []
        studentweeklist = []
        teamleaderboardlist = Team.objects.all()

        #Checks if students need to have their weekly score field reset
        for st in Student.objects.all():

            #If the student doesn't have a current question log and their week score then reset their week score
            if not st.still_current() and st.weekscore != 0:
                st.weekscore = 0
                st.save()
        #If the user is a teacher then create a list of lists of students
        #Where each list in studentteamlist is a list of the student's in one of the teacher's teams
        #Organized by score
        if hasattr(request.user, 'teacher'):

            #A teacher has a leaderboard that only contains the students who are using the same question bank as
            #the teacher's students
            teamleaderboardlist = request.user.teacher.team.all()[0].bank.team_set.all()
            teamlist = request.user.teacher.team.all()
            for i in teamlist:

                #Makes it so each entry in studentteamlist is a list of students ordered by their total score
                studentteamlist.append(i.student_set.order_by('score').reverse())

                #Makes it so each entry in studentweeklist is a list of students ordered by their weekly score
                studentweeklist.append(i.student_set.order_by('weekscore').reverse())

        #If the user is an admin then the student leaderboard will contain every team and every student in the database
        elif request.user.is_staff:
            teamlist = Team.objects.all()
            for i in teamlist:

                #Makes it so each entry in studentteamlist is a list of students ordered by their score
                studentteamlist.append(i.student_set.order_by('score').reverse())

                #Makes it so each entry in studentweeklist is a list of students ordered by their weekly score
                studentweeklist.append(i.student_set.order_by('weekscore').reverse())

        else:

            #Students can only see on the leaderboard other students using the same Question Bankm, the other
            #students using different banks are irrelevant
            teamleaderboardlist = request.user.student.team.bank.team_set.all()

        #Runs the tally score for all of the teams so that their scores will be current
        for i in Team.objects.all():
            i.tallyscore()

        #Returns data needed for each type of leaderboard
        #Week and Team use lists of teams ordered by score
        #Student uses list of lists of students ordered by score
        return render(request, 'chem/leaderboard.html', {
            'user' : request.user,

            #Teams ordered by their weekscore (used for the weekly leaderboard)
            'weekleaderboard': teamleaderboardlist.order_by('weekscore').reverse(),#Team.objects.all().order_by('weekscore').reverse(),

            #List of teams ordered by their total score (used for the Team Leaderboard)
            'teamleaderboard': teamleaderboardlist.order_by('weightedscore').reverse(),#Team.objects.all().order_by('weightedscore').reverse(),

            #A list of lists of students
            #Used for the Student Leaderboard, where students are ordered by score in their teams
            'studentleaderboard': studentteamlist,

            #A list of lists of students
            #Used for the Student Leaderboard, where students are ordered by weekly score in their teams
            'studentweekleaderboard': studentweeklist,

        })

#View that displays a list of questions
#Used to test or change parts of a question
class QuestionListView(View):

    def dispatch(self, request):

        #If the user isn't a teacher or admin redirect them to the main menu page
        if not(hasattr(request.user, 'teacher') or request.user.is_staff):
            return HttpResponseRedirect(reverse('chem:index'))

        #If a user is an admin then they can test a list of all questions
        if request.user.is_staff:
            return render(request, 'chem/questionlist.html', {
            'question_list' : Question.objects.all(),
            })

        #If a user is a teacher then they can only test the questions that the students in their
        #teams have already seen (their start time isn't in the future)
        if hasattr(request.user, "teacher"):
            banklist = []

            #Generates a list of all Question Banks the teacher's teams are a part of
            #These banks will be where the questions to be tested will be drawn from
            for i in request.user.teacher.team.all():
                if i.bank not in banklist:
                    banklist.append(i.bank)
            questionlist = []

            #Generates a list of all past and current questions a teacher's students have seen
            for i in banklist:
                for j in i.bankentry_set.all():
                    if j.starttime < timezone.now() and j.question not in questionlist:
                        questionlist.append(j.question)

            #returns the question list to the template so it can display a list of the proper questions
            return render(request, 'chem/questionlist.html', {
                'question_list': questionlist
            })


#A view that displays a random version of a question so it can be checked for errors
#You can answer it just like an actual question a student would answer and see it how it responds
class QuestionTestView(View):

    def dispatch(self, request, pk):

        #If you aren't a teacher or administrator you shouldn't be viewing this page
        #so you are sent back to the main page
        if not(hasattr(request.user, 'teacher') or request.user.is_staff):
            return HttpResponseRedirect(reverse('chem:index'))
        message = ''

        #Finds the question based on the pk in the url
        question = get_object_or_404(Question, pk=pk)

        #Generate random version of the question so it can be tested
        q = question.generate_question()
        return render(request, 'chem/questiontest.html', {
            'message': message,
            'pk': question.pk,
            'answer': q.answer.evaluate(),
            'html': question.answer().get_html(q.question_text)
        })


#View that runs function to check if the given answer is correct
#Used when testing questions
class TestGradeView(View):

    def dispatch(self, request, pk):
        if not(hasattr(request.user, 'teacher') or request.user.is_staff):
            return HttpResponseRedirect(reverse('chem:index'))

        #Finds question to be test graded
        question = get_object_or_404(Question, pk=pk)

        #The actual answer was stored in a hidden input text field with id='answer'
        actual_answer = request.POST['answer']
        q = question.generate_question()

        #Give the question's answer the Post dictionary and the actual answer
        #The is_correct_specific method will return in a given dictionary contains a given answer
        correctness = question.answer().is_correct_specific(request.POST.dict(), actual_answer)
        if correctness:
            return render(request, 'chem/questiontest.html', {
                'message': 'Correct!',
                'pk': pk,
                'answer': q.answer.evaluate(),
                'html': question.answer().get_html(q.question_text)
            })
        else:
            return render(request, 'chem/questiontest.html', {
                'message': 'Incorrect!',
                'pk': pk,
                'answer': q.answer.evaluate(),
                'html': question.answer().get_html(q.question_text)
            })


#Login function
#When the user types in their username and password and press the login button they are logged in and taken to the main menu page
#Unless an error occurs
class LoggedinView(View):

    def dispatch(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                #if hasattr(user, 'student') and user.student.defaultPass:
                #    return HttpResponseRedirect('changePass.html')
                #If the user logins they are taken to the index/mainmenu page
                return HttpResponseRedirect(reverse('chem:index'))
            else:
                return render(request, 'chem/login.html', {
                'error_message': "Your username isn't active",
                })
        else:
            return render(request, 'chem/login.html', {
                'error_message': "Your username or password isn't correct!",
                })

#Functions that runs after a question answer is submitted
#Checks if the answer is correct, updates answer and question logs, and chanegs the student's score
class GradeView(View):

    def post(self, request):

        #If the student refreshes this page after already answering they are taken back to the main menu
        if request.user.student.get_questionlog().correct:
            return HttpResponseRedirect(reverse('chem:index'))
        #If the question the student answered in no longer current (they saw the question when it was current
        #but answered it after its deadline) print out a message and dont' count their answer
        if not(request.user.student.still_current()):
            return render(request, 'chem/results.html', {'score': 0, 'message': "You missed the deadline" })

        #Gets the question log for this question so it can be updated
        qlog = request.user.student.get_questionlog()

        #If the user didn't submit an answer then tell them and don't count this as a try
        if qlog.question.answer().is_empty(request.POST.dict()):
            return render(request, 'chem/results.html', {'score': 0, 'questionlog': qlog, 'message': "You didn't type an answer" })
        qlog.tries += 1

        qlog.current_answer = str(request.POST.dict())
        qlog.current_answer_print = qlog.question.answer().print_answer(request.POST.dict())
        qlog.save()
        request.user.student.save()


        #Creates an answer log for this question answer connected to the current student
        #Fills in all of the variables based on what the question is, what the student answered, and at what time
        log = AnswerLog()
        log.student = request.user.student
        log.actual_answer = qlog.question.answer().print_answer({'question': qlog.new_answer, 'unit': '1'})
        log.student_answer = qlog.question.answer().print_answer(request.POST.dict())
        log.answer_time = timezone.now()
        log.bank = request.user.student.team.bank
        log.question_text = qlog.new_text
        log.question_start_time = qlog.start_time
        log.save()

        #Checks if the student's submitted answer was correct
        #by using the POST request sent when the user submitted their answer and converting it to a dictionary
        if request.user.student.check_answer(request.POST.dict()):
            log.correct = 1
            log.save()
            qlog.correct = True
            qlog.save()
            #Calls the function that adds to the student's score
            #Based on the score algorithm attached to the Question Bank being used
            score = request.user.student.student_score_algorithm()
            request.user.student.save()

            return render(request, 'chem/results.html', {'score': score, 'questiontext': qlog.new_text, 'questionlog': qlog, 'message': "Correct!" })
        else:
            log.correct = 0
            log.save()
            return render(request, 'chem/results.html', {'score': 0, 'questiontext': qlog.new_text, 'questionlog': qlog, 'message': "Incorrect" })


#Function that runs after the add class submit button is clicked
#Adds a group of students at one time
class addTeam(View):
    def dispatch(self, request):
        if not(hasattr(request.user, 'teacher') or request.user.is_staff):
            return HttpResponseRedirect(reverse('chem:index'))
        if "teamSize" in request.POST:
            teacher = request.user.teacher
            numStudents = int(request.POST["teamSize"])
            defaultPass = request.POST["defaultPass"]

            #Checks if the team name already exists
            if not(Team.objects.all().filter(team_name=request.POST['teamName'])):
                newTeam = Team()
                newTeam.team_name = request.POST["teamName"]
                newTeam.bank = request.user.teacher.team.all()[0].bank
                newTeam.save()
                teacher.team.add(newTeam)
                teacher.save()

            else:
                newTeam = Team.objects.all().filter(team_name=request.POST['teamName'])[0]
            for s in range(1, numStudents + 1):
                user_name = request.POST[str(s)]
                newStudent = Student()
                newStudent.user = User.objects.create_user(user_name, password=defaultPass)
                newStudent.defaultPass = True
                newStudent.school = teacher.school
                newStudent.team = newTeam
                newStudent.save()
            return HttpResponseRedirect(reverse('chem:index'))
        else:
            return render(request, 'chem/addTeam.html', {'user': request.user})


#A view that creates a list of students that a teacher can look at
#The template features various links they can use to look at the student's progress
class StudentListView(View):
    def dispatch(self, request):
        if not(hasattr(request.user, 'teacher') or request.user.is_staff):
            return HttpResponseRedirect(reverse('chem:index'))
        studentlist = []
        if request.user.is_staff:
            teamlist = Team.objects.all()
        else:
            teamlist = request.user.teacher.team.all()
        for i in teamlist:
            studentlist.append(i.student_set.all())

        #Student list is a list of students broken up into sublists based on teams
        #Team list is a list of all teams a teacher is part of
        return render(request, 'chem/studentlist.html', {'student_list': studentlist, 'team_list': teamlist})


#The view that generates a list of answer logs for a specific student
#Answer logs have data on when a student answered a question, what their answer was, and if it was correct
#Answer logs don't do anything or have any methods, they just store data for teachers and admins to look over
#to evaluate a student's performance
class AnswerLogView(View):
    def dispatch(self, request, pk):

        #If a user isn't a teacher or admin then they aren't allowed to view this page
        #They will be redirected to the main page
        if not(hasattr(request.user, 'teacher') or request.user.is_staff):
            return HttpResponseRedirect(reverse('chem:index'))
        student = get_object_or_404(Student, pk=pk)
        return render(request, 'chem/answerlog.html', {'student': student, 'loglist': student.answerlog_set.order_by('answer_time')})

#The view that generates a list of question logs for a specific student
#This shows what questions a student has seen, if they have answered, and if they are correct
#Question logs are less for displaying data and more used to keep track of what version of a question a student
#is seeing and to record data used for scoring and grading
class QuestionLogView(View):
    def dispatch(self, request, pk):
        if not(hasattr(request.user, 'teacher') or request.user.is_staff):
            return HttpResponseRedirect(reverse('chem:index'))
        student = get_object_or_404(Student, pk=pk)
        return render(request, 'chem/questionlog.html', {'student': student, 'loglist': student.questionlog_set.order_by('start_time')})


#View that changes a user's password
#A user automatically redirects here if they login with a default password
class changePass(View):
    def dispatch(self, request):
        if "newPass" in request.POST:

            #The user must type their new password twice to confirm it before it can be changed
            if request.POST["newPass"] == request.POST["passwordConfirm"]:
                request.user.set_password(request.POST["newPass"])
                if "email" in request.POST:
                    request.user.email = request.POST['email']
                request.user.student.defaultPass = False
                request.user.save()
                request.user.student.save()
                return HttpResponseRedirect(reverse('chem:login'))
        return render(request, "chem/changePass.html")


#View that has a form for changing a user's email address
class changeEmail(View):
    def dispatch(self, request):
        if "email" in request.POST:
            request.user.email = request.POST['email']
            request.user.save()
            return HttpResponseRedirect(reverse('chem:index'))
        return render(request, "chem/changeEmail.html")