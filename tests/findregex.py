# Python3 program for the
# above approach
import re

# Function that checks if a string
# contains uppercase, lowercase
# special character & numeric value
def isAllPresent(str):

	# ReGex to check if a string
	# contains uppercase, lowercase
	# special character & numeric value
	regex = ("^(?=.*[a-z])(?=." +
			"*[A-Z])(?=.*\\d)" +
			"(?=.*[-+_!@#$%^&*., ?]).+$")

	# Compile the ReGex
	p = re.compile(regex)

	# If the string is empty
	# return false
	if (str == None):
		print("No")
		return

	# Print Yes if string
	# matches ReGex
	if(re.search(p, str)):
		print("Yes")
	else:
		print("No")

# Driver code

# Given string
str = input("Enter some text: ")

#Function Call
isAllPresent(str)

# This code is contributed by avanitrachhadiya2155
