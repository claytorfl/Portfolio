from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *

class ScoreAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Name", {'fields': ['name']}),
        ('Daily Penalty Percentage', {'fields': ['per_day_penalty_percent']}),
        ('Max Daily Penalty Percentage', {'fields': ['max_day_penalty']}),
        ('Wrong Answer Penalty Percentage', {'fields': ['per_wrong_answer_penalty_percent']}),
        ('Max Wrong Answer Penalty Percentage', {'fields': ['max_wrong_answer_penalty']}),

    ]



#Admin class that displays parameters for a question
class ParameterInLine(admin.TabularInline):
    model = Parameter
    can_delete =True
    verbose_name_plural = 'Parameter'

#Admin class that displays the UnitDropDown models for a question
class UnitInLine(admin.TabularInline):
    model = UnitDropDown
    can_delete =True
    verbose_name_plural = 'Unit'

#Admin class that displays a form to enter the data for a Math Answer
class MathAnswerInLine(admin.TabularInline):
    model = MathAnswer
    can_delete =True
    verbose_name_plural = 'Math Answer'

#Admin class that displays a form to enter the data for a Balancing Equation Answer
class BalanceAnswerInLine(admin.TabularInline):
    model = BalanceAnswer
    can_delete =True
    verbose_name_plural = 'Balance Answer'


#Admin Page info for adding Questions
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Question Title', {'fields': ['question_text']}),

    ]
    inlines = [MathAnswerInLine, BalanceAnswerInLine, ParameterInLine, UnitInLine]

    list_display = ['question_text']


#Admin Page info for adding Schools
class SchoolAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name', {'fields': ['name']}),
    ]

    list_display = ['name']

#Admin Page info for adding Teams
class TeamAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name', {'fields': ['team_name']}),
        ('Question Bank', {'fields': ['bank']}),
    ]

    list_display = ['team_name']

#Admin class to display form for adding Student info to a user
class StudentInline(admin.StackedInline):
    model = Student
    can_delete =True
    verbose_name_plural = 'student'

#Admin class to display form for adding Teacher info to a user
class TeacherInline(admin.StackedInline):
    model = Teacher
    can_delete = True
    verbose_name_plural = 'teacher'


# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = [StudentInline, TeacherInline]

#Admin class to display Bank Entry forms on the Question Bank
class BankEntryInline(admin.TabularInline):
    model = BankEntry
    can_delete = True
    verbose_name_plural = 'entries'

#Admin Page for adding a Question Bank (this gives a list of questions to a Team)
class QuestionBankAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name', {'fields': ['name']}),
        ('Max Score', {'fields': ['max_score']}),
        ('Team Scoring Algorithm', {'fields': ['scorer']}),
    ]
    inlines = [BankEntryInline]

class QuestionLogAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Text', {'fields': ['new_text']}),
    ]

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(QuestionBank, QuestionBankAdmin)
admin.site.register(QuestionLog, QuestionLogAdmin)
admin.site.register(ScoreAlgorithm, ScoreAdmin)