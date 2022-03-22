from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib import messages


class Professor(models.Model):

	# unique id
	name = models.CharField(max_length = 64)
	professor_id = models.CharField(max_length = 8, unique = True)


	def __str__(self):
		return U"%s (%s)" % (self.name, self.professor_id)


class Module(models.Model):

	# semester 1 or 2
	SEMESTERS = [(i,i) for i in range(1, 3)]

	# years 2015 - 2025
	YEARS = [(i,i) for i in range(2015, 2026)]

	# module info
	module_name = models.CharField(max_length = 64)
	module_code = models.CharField(max_length = 16)
	year = models.IntegerField(choices = YEARS)
	semester =  models.IntegerField(choices = SEMESTERS)

	# professors associated with the module
	professors = models.ManyToManyField(Professor, blank = True)

	# override clean() to perform an additioanl validation
	# ensure that the module name and code are either both unique (completely new module)
	# or a module with given name and code already exists (same module, but we want to change year or semester)
	def clean(self):
		cleaned_data = super(Module, self).clean()

		if (not Module.objects.filter(module_name = self.module_name, module_code = self.module_code).exists()
			and (Module.objects.filter(module_code = self.module_code).exists() or Module.objects.filter(module_name = self.module_name).exists())):

			raise ValidationError({'module_name': ["A module with either the given name or code already exists."]})

		return cleaned_data

	class Meta:

		# we have already checked the name and code
		# check that the instance itself is unique
		# the instance is unqiue if at least one of the four fields below is unique
		constraints = [models.UniqueConstraint(fields = ["module_name", "module_code", "year", "semester"], name = 'unique_module_instance')]

	def __str__(self):
		return U"%s (%s)" % (self.module_name, self.module_code)



class Rating(models.Model):

	# ratings 1 - 5
	RATINGS = [(i,i) for i in range(1, 6)]
	rating = models.IntegerField(choices = RATINGS)

	# the user who gave the rating
	student_id = models.CharField(max_length = 64)

	# foreign keys
	module = models.ForeignKey(Module, on_delete = models.CASCADE, blank = True)
	professor = models.ForeignKey(Professor, on_delete = models.CASCADE, blank = True)

	# check that the rating is unique
	class Meta:
		constraints = [models.UniqueConstraint(fields = ["professor", "module", "student_id"], name = 'unique_rating')]

	def __str__(self):
		return U"%i star(s) for professor %s in module %s" % (self.rating, self.professor.name, self.module.module_name)
