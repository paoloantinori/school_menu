import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from school_menu.forms import SchoolForm
from school_menu.models import DetailedMeal, School, SimpleMeal
from school_menu.serializers import MealSerializer


# TODO: need to refactor this function when number of weeks is different than 4 in settings
def calculate_week(week, bias):
    """
    Getting week number from today's date translated to week number available in Meal model (1,2,3,4) shifted by bias
    """
    week_number = (week + bias) / 4
    floor_week_number = (week + bias) // 4
    if week_number == floor_week_number:
        return 4
    else:
        return int((week_number - floor_week_number) * 4)


def get_current_date():
    """
    Get current week and day
    """
    today = datetime.datetime.now()
    current_year, current_week, current_day = today.isocalendar()
    # get next week monday's menu on weekends
    if current_day > 5:
        current_week = current_week + 1
        adjusted_day = 1
    else:
        adjusted_day = current_day
    return current_week, adjusted_day


def index(request):
    context = {}
    if request.user.is_authenticated:
        school = School.objects.filter(user=request.user).first()
        if not school:
            redirect("school_menu:settings")
        current_week, adjusted_day = get_current_date()
        bias = school.week_bias
        adjusted_week = calculate_week(current_week, bias)
        season = school.season_choice
        # TODO: need to degrade better when menu for the day is not available
        if school.menu_type == School.Types.SIMPLE:
            weekly_meals = SimpleMeal.objects.filter(
                school=school, week=adjusted_week, season=season
            ).order_by("day")
            meal_for_today = weekly_meals.get(day=adjusted_day)
        else:
            weekly_meals = DetailedMeal.objects.filter(
                school=school, week=adjusted_week, season=season
            ).order_by("day")
            meal_for_today = weekly_meals.get(day=adjusted_day)
        context = {
            "school": school,
            "meal": meal_for_today,
            "weekly_meals": weekly_meals,
            "week": adjusted_week,
            "day": adjusted_day,
        }
    return render(request, "index.html", context)


def school_menu(request, slug):
    """Return school menu for the given school"""
    school = get_object_or_404(School, slug=slug)
    current_week, adjusted_day = get_current_date()
    bias = school.week_bias
    adjusted_week = calculate_week(current_week, bias)
    season = school.season_choice
    # TODO: need to degrade better when menu for the day is not available
    if school.menu_type == School.Types.SIMPLE:
        weekly_meals = SimpleMeal.objects.filter(
            school=school, week=adjusted_week, season=season
        ).order_by("day")
        meal_for_today = weekly_meals.get(day=adjusted_day)
    else:
        weekly_meals = DetailedMeal.objects.filter(
            school=school, week=adjusted_week, season=season
        ).order_by("day")
        meal_for_today = weekly_meals.get(day=adjusted_day)
    context = {
        "school": school,
        "meal": meal_for_today,
        "weekly_meals": weekly_meals,
        "week": adjusted_week,
        "day": adjusted_day,
    }
    return render(request, "school-menu.html", context)


def get_menu(request, week, day, type, school_id):
    """get menu for the given school, day, week and type"""
    school = School.objects.get(pk=school_id)
    season = school.season_choice
    if school.menu_type == School.Types.SIMPLE:
        weekly_meals = SimpleMeal.objects.filter(
            week=week, type=type, season=season, school=school
        ).order_by("day")
    else:
        weekly_meals = DetailedMeal.objects.filter(
            week=week, type=type, season=season, school=school
        ).order_by("day")
    meal_of_the_day = weekly_meals.get(day=day)
    context = {
        "school": school,
        "meal": meal_of_the_day,
        "weekly_meals": weekly_meals,
        "week": week,
        "day": day,
        "type": type,
    }
    return render(request, "partials/_menu.html", context)


@require_http_methods(["GET"])
def json_menu(request):
    current_week, adjusted_day = get_current_date()
    adjusted_week = calculate_week(current_week, 0)
    season = School.objects.first().season_choice
    meal_for_today = DetailedMeal.objects.filter(
        week=adjusted_week, type=1, season=season
    )
    serializer = MealSerializer(meal_for_today, many=True)
    meals = list(serializer.data)
    data = {"current_day": adjusted_day, "meals": meals}
    return JsonResponse(data, safe=False)


@login_required
def settings_view(request, pk):
    User = get_user_model()
    queryset = User.objects.select_related("school")
    user = get_object_or_404(queryset, pk=pk)
    context = {"user": user}
    return render(request, "settings.html", context)


@login_required
def school_view(request):
    user = request.user
    school = get_object_or_404(School, user=user)
    context = {"school": school}
    return render(request, "settings.html#school", context)


@login_required
def school_create(request):
    form = SchoolForm(request.POST or None)
    if form.is_valid():
        school = form.save(commit=False)
        school.user = request.user
        school.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            f"<strong>{school.name}</strong> created successfully",
        )
        return render(request, "settings.html#school", {"school": school})

    context = {"form": form, "create": True}
    return render(request, "partials/school.html", context)


@login_required
def school_update(request):
    school = get_object_or_404(School, user=request.user)
    form = SchoolForm(request.POST or None, instance=school)
    if form.is_valid():
        school = form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            f"<strong>{school.name}</strong> updated successfully",
        )
        return render(request, "settings.html#school", {"school": school})

    context = {"form": form}
    return render(request, "partials/school.html", context)


def school_list(request):
    schools = School.objects.all()
    context = {"schools": schools}
    return TemplateResponse(request, "school-list.html", context)
