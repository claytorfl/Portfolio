from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from . import views

#Contains all url's that come after chem in the url
urlpatterns = [



    #Url the user goes to immediately after logging in. Displays the question and has links to other parts of site
    url(r'^menu$', views.MainMenuView.as_view(), name='index'),

    #URL for the view that has forms for teacher's to add a class of students quickly (addclass function still being added so this is commented out
    url(r'^addTeam$', views.addTeam.as_view(), name='addTeam'),

    #URL that calls function to add the students entered in the form from the above URL
    url(r'^addClass', views.addTeam.as_view(), name='addClass'),

    #URL that runs the grade function to see if the submitted answer is right or wrong
    url(r'^grade/$', views.GradeView.as_view(), name='grade'),

    #The first page users see, has forms for logging in
    url(r'^$', views.LoginView.as_view(), name='login'),

    #Function that logs users in and then redirects them to the main menu
    url(r'^logged$', views.LoggedinView.as_view(), name='logged'),

    #URL that calls function to logout the user and redirect them back to the login page
    url(r'^logout$', views.LogOutView.as_view(), name='logout'),

    #The url for the leaderboard page that contains links to all other leaderboards
    url(r'^leaderboard$', views.LeaderboardView.as_view(), name='leaderboard'),

    #The url that shows the answer logs for a particular student
    url(r'^(?P<pk>[0-9]+)/answerlog$', views.AnswerLogView.as_view(), name='answerlog'),

    #The url that shows the question logs for a particular student
    url(r'^(?P<pk>[0-9]+)/questionlog$', views.QuestionLogView.as_view(), name='questionlog'),

    #URL that shows a list of all of a teacher's students so they can look at their answer logs, other info,
    #or edit them in some way
    url(r'^studentlist$', views.StudentListView.as_view(), name='studentlist'),

    #URL that displays a list of all questions so the admin can test or edit them
    url(r'^questionlist$', views.QuestionListView.as_view(), name='questionlist'),

    #URL that displays a question and a form to answer it so the question can be tested
    url(r'^(?P<pk>[0-9]+)/test$', views.QuestionTestView.as_view(), name='questiontest'),

    #URL that runs the function to grade the test question answer
    url(r'^(?P<pk>[0-9]+)/testgrade$', views.TestGradeView.as_view(), name='testgrade'),


    #Url for the change password template
    #Used when a user has a default password or just feels like changing their password
    url(r'^changepassword$', views.changePass.as_view(), name='changePass'),

    #URL for the change email template
    #Every user needs an email so they can use the Forgot Password function
    url(r'^changeemail$', views.changeEmail.as_view(), name='changeEmail'),
]