from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import IntegrityError
from .models import Module, Professor, Rating

import json, math

@csrf_exempt
def user_login(request):

    if (request.method != "POST"):
        return HttpResponseBadRequest("invalid request method.", content_type = "plain/text")

    # retrieve username and password
    request_data = json.loads(request.body)

    # check credentials
    user = authenticate(username = request_data["username"], password = request_data["password"])

    if user is not None:

        if user.is_active:

            # bind to the session
            login(request, user)

            response = HttpResponse("login successful: welcome, " + request_data["username"], content_type = "plain/text")
            response.status_code = 200
            response.reasonphrase = "OK"

            return response

        return HttpResponseBadRequest("inactive account", content_type = "plain/text")

    return HttpResponseBadRequest("invalid credentials", content_type = "plain/text")



@csrf_exempt
def user_register(request):

    # check http method
    if request.method != "POST":
        return HttpResponseBadRequest("invalid request method.", content_type = "plain/text")


    # check if user is logged in
    if request.user.is_authenticated:
        return HttpResponseBadRequest("cannot register a new user while logged in", content_type = "plain/text")


    request_data = json.loads(request.body)

    # check if username already exists
    if User.objects.filter(username = request_data["username"]).exists():
        return HttpResponseBadRequest("registration failed: username exists", content_type = "plain/text")

    # if not, create new user
    User.objects.create_user(username = request_data["username"], password = request_data["password"])

    # respond to client
    response = HttpResponse("registration successful: welcome, " + request_data["username"], content_type = "plain/text")
    response.status_code = 200
    response.reasonphrase = "OK"

    return response



@csrf_exempt
def user_logout(request):

    if request.method != "POST":
        return HttpResponseBadRequest("invalid request method.", content_type = "plain/text")

    # check if user is logged in
    if not request.user.is_authenticated:
        return HttpResponseBadRequest("login is required to use this function", content_type = "plain/text")

    # unbind from the session
    logout(request)

    response = HttpResponse("successfully logged out", content_type = "plain/text")
    response.status_code = 200
    response.reasonphrase = "OK"

    return response



@csrf_exempt
def list_modules(request):

    if request.method != "GET":
        return HttpResponseBadRequest("invalid request method.", content_type = "plain/text")

    # check if user is logged in
    if not request.user.is_authenticated:
        return HttpResponseBadRequest("login is required to use this function", content_type = "plain/text")

    request_data = json.loads(request.body)

    response_data = {"num_items" : "0", "items" : []}

    num_items = 0

    # iterate over all module instances
    for module in Module.objects.all():

        num_professors = 0
        num_items += 1

        module_info = {"module_name" : "", "module_code" : "", "year" : "", "semester" : "", "num_professors" : "", "professors" : [], "professors_id" : [] }

        # general module info
        module_info["module_name"] = module.module_name
        module_info["module_code"] = module.module_code
        module_info["semester"] = str(module.semester)
        module_info["year"] = str(module.year)

        # related professors
        for professor in module.professors.all():
            num_professors += 1
            module_info["professors"].append(professor.name)
            module_info["professors_id"].append(professor.professor_id)

        module_info["num_professors"] = str(num_professors)
        response_data["num_items"] = str(num_items)
        response_data["items"].append(module_info)

    response = HttpResponse(json.dumps(response_data), content_type = "application/json")
    response.status_code = 200
    response.reasonphrase = "OK"

    return response



@csrf_exempt
def view_professors(request):

    if request.method != "GET":
        return HttpResponseBadRequest("invalid request method.", content_type = "plain/text")

    # check if user is logged in
    if not request.user.is_authenticated:
        return HttpResponseBadRequest("login is required to use this function", content_type = "plain/text")

    response_data = {"names" : [], "professor_ids" : [], "ratings" : []}

    # iterate over all professors
    for professor in Professor.objects.all():
        response_data["names"].append(professor.name)
        response_data["professor_ids"].append(professor.professor_id)

        srating = 0
        nrating = 0

        # retrieve each professor's ratings
        for rating in professor.rating_set.all():
            nrating += 1
            srating += rating.rating

        # no ratings yet
        if srating == 0 and nrating == 0:
            response_data["ratings"].append("No ratings yet")

        else:
            avi = 0

            # get average
            if (srating / nrating) - math.floor(srating / nrating) < 0.5:
                avi = math.floor(srating / nrating)
            else:
                avi = math.ceil(srating / nrating)

            # convert numbers to asterisks
            astisks = ""
            for astisk in range(avi):
                astisks += "*"
            response_data["ratings"].append(astisks)

    response = HttpResponse(json.dumps(response_data), content_type = "application/json")
    response.status_code = 200
    response.reasonphrase = "OK"

    return response



@csrf_exempt
def average_rating(request):

    if request.method != "GET":
        return HttpResponseBadRequest("invalid request method.", content_type = "plain/text")

    # check if user is logged in
    if not request.user.is_authenticated:
        return HttpResponseBadRequest("login is required to use this function", content_type = "plain/text")

    request_data = json.loads(request.body)

    # check that the module exists with this code exists
    if not Module.objects.filter(module_code = request_data["module_code"]).exists():
        return HttpResponseBadRequest("such module does not exist", content_type = "plain/text")

    # check that the professor exists
    if not Professor.objects.filter(professor_id = request_data["professor_id"]).exists():
        return HttpResponseBadRequest("such professor does not exist", content_type = "plain/text")

    # the professor
    professor = Professor.objects.get(professor_id = request_data["professor_id"])

    # check that the professor teaches at least one module with code provided in the request
    if not Module.objects.filter(module_code = request_data["module_code"], professors = professor).exists():
        return HttpResponseBadRequest("such professor does not teach any modules with code " + request_data["module_code"], content_type = "plain/text")

    # retrieve all ratings of the professor, where the module code in a rating matches the request
    if not professor.rating_set.all().filter(module__module_code = request_data["module_code"]).exists():
        return HttpResponseBadRequest("such professor does not have any ratings for modules with code " + request_data["module_code"], content_type = "plain/text")

    ratings = professor.rating_set.all().filter(module__module_code = request_data["module_code"])
    nrating = 0
    srating = 0

    # compute average
    for rating in ratings:
        srating += rating.rating
        nrating += 1

    avi = 0

    # get average
    if (srating / nrating) - math.floor(srating / nrating) < 0.5:
        avi = math.floor(srating / nrating)
    else:
        avi = math.ceil(srating / nrating)

    # compute average rating in asterisks
    astisks = ""
    for astisk in range(avi):
        astisks += "*"

    module = Module.objects.filter(module_code = request_data["module_code"]).first()

    response = HttpResponse("average of " + professor.name + " (" + professor.professor_id + ") in module " + module.module_name + " (" + module.module_code + ") " + " is: " + astisks, content_type = "plain/text")
    response.status_code = 200
    response.reasonphrase = "OK"

    return response



@csrf_exempt
def rate_professor(request):

    if request.method != "POST":
        return HttpResponseBadRequest("invalid request method.", content_type = "plain/text")

    # check if user is logged in
    if not request.user.is_authenticated:
        return HttpResponseBadRequest("login is required to use this function", content_type = "plain/text")

    request_data = json.loads(request.body)

    # check that the rating is valid
    if not request_data["rating"].isdigit():
        return HttpResponseBadRequest("provided rating is not a number", content_type = "plain/text")

    if int(request_data["rating"]) > 5 or int(request_data["rating"]) < 1:
        return HttpResponseBadRequest("rating has to be an integer between 1 and 5", content_type = "plain/text")

    # check that the module instance exists
    if not Module.objects.filter(module_code = request_data["module_code"], year = int(request_data["year"]), semester = int(request_data["semester"])).exists():
        return HttpResponseBadRequest("such module does not exist", content_type = "plain/text")

    # check that the professor exists
    if not Professor.objects.filter(professor_id = request_data["professor_id"]).exists():
        return HttpResponseBadRequest("such professor does not exist", content_type = "plain/text")

    professor = Professor.objects.get(professor_id = request_data["professor_id"])
    module = Module.objects.get(module_code = request_data["module_code"], year = int(request_data["year"]), semester = int(request_data["semester"]))

    # check that the professor teaches the said module instance
    if not module.professors.filter(professor_id = professor.professor_id).exists():
        return HttpResponseBadRequest("such professor does not teach this module", content_type = "plain/text")

    # check that this professor hasn't already been rated by this student for this module instance
    if Rating.objects.filter(student_id = request.user.username, module = module, professor = professor).exists():
        return HttpResponseBadRequest("you have already rated this professor for this module", content_type = "plain/text")

    # create the rating
    rating = Rating.objects.create(rating = int(request_data["rating"]), student_id = request.user.username, module = module, professor = professor)

    response = HttpResponse("professor successfully rated", content_type = "plain/text")
    response.status_code = 200
    response.reasonphrase = "OK"

    return response
