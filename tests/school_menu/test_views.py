from unittest.mock import patch

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from pytest_django.asserts import assertTemplateUsed

from school_menu.models import DetailedMeal, School, SimpleMeal
from school_menu.test import TestCase
from tests.school_menu.factories import (
    DetailedMealFactory,
    SchoolFactory,
    SimpleMealFactory,
)
from tests.users.factories import UserFactory


def create_formset_post_data(response, new_form_data=None):
    """Create the formset payload for a post() using the response obtained from a get() request."""
    if new_form_data is None:
        new_form_data = []
    csrf_token = response.context["csrf_token"]
    formset = response.context["formset"]
    prefix_template = formset.empty_form.prefix  # default is 'form-__prefix__'

    # Extract initial formset data
    management_form_data = formset.management_form.initial
    form_data_list = (
        formset.initial if formset.initial is not None else []
    )  # Ensure form_data_list is a list

    # Add new form data and update management form data
    form_data_list.extend(new_form_data)
    management_form_data["TOTAL_FORMS"] = len(form_data_list)

    # Initialize the post data dict
    post_data = dict(csrf_token=csrf_token)

    # Add properly prefixed management form fields
    for key, value in management_form_data.items():
        prefix = prefix_template.replace("__prefix__", "")
        post_data[prefix + key] = value

    # Add properly prefixed data form fields
    for index, form_data in enumerate(form_data_list):
        for key, value in form_data.items():
            prefix = prefix_template.replace("__prefix__", f"{index}-")
            post_data[prefix + key] = value

    return post_data


class IndexView(TestCase):
    def test_get(self):
        response = self.get("school_menu:index")

        self.response_200(response)
        assertTemplateUsed(response, "index.html")

    def test_get_with_authenticated_user_and_no_school(self):
        user = self.make_user()
        redirect_url = self.reverse("school_menu:settings", pk=user.pk)

        with self.login(user):
            response = self.get("school_menu:index")

        assert response.status_code == 302
        assert response.url == redirect_url

    def test_get_with_authenticated_user(self):
        user = self.make_user()
        school = SchoolFactory(user=user)

        with self.login(user):
            response = self.get("school_menu:index")

        self.response_200(response)
        assert response.context["school"] == school

    def test_get_with_detailed_meal_setting(self):
        user = self.make_user()
        school = SchoolFactory(user=user, menu_type=School.Types.DETAILED)

        with self.login(user):
            response = self.get("school_menu:index")

        self.response_200(response)
        assert response.context["school"] == school


class SchoolMenuView(TestCase):
    def test_get(self):
        school = SchoolFactory()
        response = self.get("school_menu:school_menu", slug=school.slug)

        self.response_200(response)
        assertTemplateUsed(response, "school-menu.html")
        assert response.context["school"] == school

    def test_get_with_detailed_menu(self):
        school = SchoolFactory(menu_type=School.Types.SIMPLE)
        response = self.get("school_menu:school_menu", slug=school.slug)

        self.response_200(response)
        assertTemplateUsed(response, "school-menu.html")
        assert response.context["school"] == school


class GetMenuView(TestCase):
    def test_get_with_simple_menu(self):
        school = SchoolFactory(
            menu_type=School.Types.SIMPLE, season_choice=School.Seasons.PRIMAVERILE
        )
        meal = SimpleMealFactory(
            school=school,
            day=1,
            week=1,
            menu="Pasta al Pomodoro",
            snack="Crackers",
            season=School.Seasons.PRIMAVERILE,
        )

        response = self.get("school_menu:get_menu", 1, 1, 1, school.pk)

        self.response_200(response)
        assert response.context["meal"] == meal

    def test_get_with_detailed_menu(self):
        school = SchoolFactory(
            menu_type=School.Types.DETAILED, season_choice=School.Seasons.PRIMAVERILE
        )
        meal = DetailedMealFactory(
            school=school,
            day=1,
            week=1,
            first_course="Pasta al Pomodoro",
            snack="Crackers",
            season=School.Seasons.PRIMAVERILE,
        )

        response = self.get("school_menu:get_menu", 1, 1, 1, school.pk)

        self.response_200(response)
        assert response.context["meal"] == meal


class SettingView(TestCase):
    def test_get(self):
        user = self.make_user()
        SchoolFactory(user=user)

        with self.login(user):
            response = self.get("school_menu:settings", pk=user.pk)

        self.response_200(response)
        assertTemplateUsed(response, "settings.html")
        assert response.context["user"] == user

    def test_partial_reload(self):
        user = self.make_user()
        SchoolFactory(user=user)

        with self.login(user):
            response = self.get("school_menu:menu_settings", pk=user.pk)

        self.response_200(response)
        assert response.context["user"] == user

    def test_school_partial_view(self):
        user = self.make_user()
        school = SchoolFactory(user=user)

        with self.login(user):
            response = self.get("school_menu:school_view")

        self.response_200(response)
        assert response.context["school"] == school

    def test_school_create_with_success(self):
        user = self.make_user()
        data = {
            "name": "Test School",
            "city": "Milano",
            "season_choice": School.Seasons.INVERNALE,
            "week_bias": 1,
            "menu_type": School.Types.DETAILED,
        }

        with self.login(user):
            response = self.post("school_menu:school_create", data=data)
            school = School.objects.get(user=user)

        self.response_200(response)
        message = list(get_messages(response.wsgi_request))[0].message
        assert message == f"<strong>{ school.name }</strong> creata con successo"
        assert School.objects.filter(user=user).count() == 1
        assert school.name == "Test School"

    def test_school_create_with_invalid_data(self):
        user = self.make_user()
        data = {
            "name": "",
        }

        with self.login(user):
            response = self.post("school_menu:school_create", data=data)

        self.response_200(response)
        assert School.objects.filter(user=user).count() == 0

    def test_school_update_with_success(self):
        user = self.make_user()
        school = SchoolFactory(user=user)
        data = {
            "name": "Test School",
            "city": "Milano",
            "season_choice": School.Seasons.INVERNALE,
            "week_bias": 1,
            "menu_type": School.Types.DETAILED,
        }

        with self.login(user):
            response = self.post("school_menu:school_update", data=data)

        self.response_200(response)
        school = School.objects.get(user=user)
        message = list(get_messages(response.wsgi_request))[0].message
        assert message == f"<strong>{ school.name }</strong> aggiornata con successo"
        assert school.city == "Milano"

    def test_school_update_with_invalid_data(self):
        user = self.make_user()
        SchoolFactory(user=user)
        data = {
            "name": "",
        }

        with self.login(user):
            response = self.post("school_menu:school_update", data=data)

        self.response_200(response)


class SchoolListView(TestCase):
    def test_get(self):
        SchoolFactory.create_batch(3)
        school = School.objects.first()

        response = self.get("school_menu:school_list")

        self.response_200(response)
        assertTemplateUsed(response, "school-list.html")
        assert school in response.context["schools"]


class UploadMenuView(TestCase):
    def test_get(self):
        user = self.make_user()
        school = SchoolFactory(user=user)

        with self.login(user):
            response = self.get("school_menu:upload_menu", school.pk)

        self.response_200(response)
        assertTemplateUsed(response, "upload-menu.html")
        assert response.context["school"] == school

    @patch("school_menu.views.import_menu")
    def test_post_with_valid_data(self, mock_import_menu):
        user = self.make_user()
        school = SchoolFactory(user=user)
        data = {
            "file": SimpleUploadedFile(
                "test_menu.xlsx",
                b"these are the file contents!",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            "season": School.Seasons.INVERNALE,
        }

        with self.login(user):
            response = self.post("school_menu:upload_menu", school.pk, data=data)

        self.response_204(response)
        mock_import_menu.assert_called_once()

    def test_post_with_invalid_data(self):
        user = self.make_user()
        school = SchoolFactory(user=user)
        data = {
            "season": "WINTER",
        }

        with self.login(user):
            response = self.post("school_menu:upload_menu", school.pk, data=data)

        self.response_200(response)
        assertTemplateUsed(response, "upload-menu.html")
        assert "form" in response.context
        assert "file" in response.context["form"].errors


class CreateWeeklyMenuView(TestCase):
    def test_get(self):
        user_factory = UserFactory  # noqa
        menu_types = [School.Types.SIMPLE, School.Types.DETAILED]
        for index, menu_type in enumerate(menu_types):
            user = self.make_user(index)
            school = SchoolFactory(menu_type=menu_type, user=user)

            with self.login(user):
                response = self.get("school_menu:create_weekly_menu", school.pk, 1, 1)

            self.response_200(response)
            assert "formset" in response.context
            assertTemplateUsed(response, "create-weekly-menu.html")
            assert response.context["school"] == school
            assert response.context["week"] == 1
            assert response.context["season"] == 1
            if menu_type == School.Types.SIMPLE:
                assert SimpleMeal.objects.filter(school=school).count() == 5
            else:
                assert DetailedMeal.objects.filter(school=school).count() == 5

    def test_get_with_meals_already_present(self):
        user = self.make_user()
        school = SchoolFactory(user=user, menu_type=School.Types.SIMPLE)
        SimpleMealFactory.create_batch(5, school=school)

        with self.login(user):
            response = self.get("school_menu:create_weekly_menu", school.pk, 1, 1)

        self.response_200(response)
        assert "formset" in response.context
        assertTemplateUsed(response, "create-weekly-menu.html")
        assert response.context["school"] == school
        assert response.context["week"] == 1
        assert response.context["season"] == 1
        assert SimpleMeal.objects.filter(school=school).count() == 5

    def test_post_with_valid_data(self):
        user = self.make_user()
        school = SchoolFactory(menu_type=School.Types.SIMPLE, user=user)
        test_data = [
            {"id": 1, "day": 1, "menu": "Pasta al Pomodoro", "snack": "Crackers"},
            {"id": 2, "day": 2, "menu": "Riso al Sugo", "snack": "Yogurt"},
            {"id": 3, "day": 3, "menu": "Pasta al Pesto", "snack": "Frutta"},
            {"id": 4, "day": 4, "menu": "Riso al Tonno", "snack": "Crackers"},
            {"id": 5, "day": 5, "menu": "Pasta al Ragù", "snack": "Yogurt"},
        ]

        with self.login(user):
            response = self.get("school_menu:create_weekly_menu", school.pk, 1, 1)
            self.response_200(response)
            post_data = create_formset_post_data(response, new_form_data=test_data)
            response = self.post(
                "school_menu:create_weekly_menu", school.pk, 1, 1, data=post_data
            )

        self.response_302(response)
        assert response.url == self.reverse("school_menu:settings", school.user.pk)

    def test_post_with_invalid_data(self):
        user = self.make_user()
        school = SchoolFactory(menu_type=School.Types.SIMPLE, user=user)
        test_data = [
            {"id": 1, "day": 1, "menu": "Pasta al Pomodoro", "snack": "Crackers"},
            {"id": 2, "day": 2, "menu": "Riso al Sugo", "snack": "Yogurt"},
            {"id": 3, "day": 3, "menu": "Pasta al Pesto", "snack": "Frutta"},
            {"id": 4, "day": 4, "menu": "Riso al Tonno", "snack": "Crackers"},
            {"id": 5, "day": 5, "menu": "Pasta al Ragù", "snack": "Yogurt"},
        ]

        with self.login(user):
            response = self.get("school_menu:create_weekly_menu", school.pk, 1, 1)
            self.response_200(response)
            post_data = create_formset_post_data(response, new_form_data=test_data)
            post_data["form-0-menu"] = ""
            response = self.post(
                "school_menu:create_weekly_menu", school.pk, 1, 1, data=post_data
            )

        self.response_200(response)
        assert "formset" in response.context
        assert response.context["formset"].errors


class SchoolSearchView(TestCase):
    def setUp(self):
        self.test_school = SchoolFactory(name="Test School", city="Milano")
        SchoolFactory.create_batch(10)

    def test_get_with_school_name(self):
        response = self.get("school_menu:search_schools", data={"q": "test"})

        self.response_200(response)
        assert "Test School" in response.content.decode()

    def test_get_with_school_city(self):
        response = self.get("school_menu:search_schools", data={"q": "milano"})

        self.response_200(response)
        assert "Milano" in response.content.decode()

    def test_with_empty_input(self):
        response = self.get("school_menu:search_schools", data={"q": ""})

        self.response_200(response)

    def test_with_no_school_matching_search(self):
        response = self.get(
            "school_menu:search_schools", data={"q": "kjsdkjhsdkjhkslk"}
        )

        self.response_200(response)
        assert (
            "Nessuna scuola soddisfa i criteri di ricerca..."
            in response.content.decode()
        )

    # def test_with_index_page_referer(self):
    #     self.get(
    #         "school_menu:search_schools",
    #         data={"q": "test"},
    #         extra={"HTTP_REFERER": "localhost:8000/"},
    #     )

    #     self.assertResponseHeaders({'HTTP_REFERER': 'localhost:8000/'})
