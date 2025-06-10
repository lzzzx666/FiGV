
input_filter = '''

Please evaluate the input question based on the following four elements and provide detailed feedback:

Clarity of the question: Is the question expressed clearly, and is its meaning easy to understand?
Specificity of the question: Is the question specific? Does it provide detailed information about what is needed?
Answerability of the question: Does the question provide enough information to be answered, or can the model rely on its own knowledge to answer it?
Reasonableness of the question: Is the question reasonable? Is it a declarative sentence (a declarative sentence does not require an answer) and a real question that a user might ask?

Please rate each element on a scale of 1 to 5 (1 being very poor, and 5 being very good), and briefly explain the reason for the rating. Finally, calculate an overall score based on the average rating of each element, and output this total score on the last line.

Example:
Question 1: What is showing high value?",
Clarity: 1 - The question is relatively vague, it does not clearly express a specific meaning, the concept of "showing high value" is not clear, and it is hard to understand.
Specificity: 1 - The question lacks detailed information and does not provide enough context or situation to clarify what "showing high value" refers to, making it difficult to judge in what field or context it is being discussed.
Answerability: 1 - Since the question is too general and vague and does not provide enough information, it is difficult for the model to provide a definite answer based on existing knowledge.
Reasonableness: 2 - Although the question is vague, asking about "value" is indeed a question a user might ask, but it needs more detail and background explanation.
Total Score: 1.25

Question 2: Write a Python script to publish a new blog post on my WordPress website.
Clarity: 4 - This question is relatively clear, although it could include some background information, such as whether there is a specific WordPress API configuration.
Specificity: 3 - Although the question has specified writing a Python script to publish content on WordPress, it lacks some specific details, like the content of the blog post, the version of the WordPress API, or specific requirements like supporting multimedia content publishing.
Answerability: 4 - Even though specific blog content and API configuration details are not provided, the model can give a typical solution using Python and WordPress API based on general knowledge. Therefore, the question is still answerable.
Reasonableness: 5 - This is a very reasonable question; users may often encounter the need to automate the publishing of blog posts in practical applications.
Total Score: 4

Please evaluate the following question and output the total score on the last line, note that if the question is not in English, the Total Score should be 0:

Question: {}
Evaluation:
'''


constraint_format = '''

As an expert in contextual language constraints, you will create {}  constraints and combine them with the original instruction to generate a new, more complex instruction.
When creating these constraints, you should first identify a general category that encompasses the overall restrictions you wish to impose.
Also, be mindful that constraints should not be mistaken for additional information or descriptions; they are merely to narrow the potential response scope.
Furthermore, you need to consider whether the added constraints align with the original instruction, whether the instruction with added constraints is reasonable and likely to be a real instruction that a user might issue, and whether it is excessively rigid.

These are the categories of constraints that have been provided for you to choose from, if they are not suitable, you can also create your own constraints:
{}


Please note that your response should only return the new instruction without any additional information (such as the added constraints and the justification for the instruction's reasonableness). Do not include words like "The new instruction is:"!!!

Here is my original instruction: {}.
The new instruction is:
'''


constraints_list = [
    "Keyword Usage: \n Description: Ensuring the use of specific keywords or avoiding certain forbidden words in the text. This includes requirements for the number, frequency, occurrence of specific letters, and placement of keywords. \n Example: \n - Keywords existence \n - Forbidden words \n - Keywords frequency \n - Letter frequency in keywords \n - Keywords in specific positions",
    "Language Style: \n Description: Adhering to specific language style or tone in the response, such as using a particular dialect or regional language, adopting a formal or informal tone, using gender-specific or gender-neutral language, or employing idioms or colloquial expressions. \n Example: \n - Constraints on what kinds of Language should be used in response \n - Specific dialects or regional language constraints \n - Formal or informal tone \n - Gender-specific / Gender-neutral language \n - Use of idioms or colloquial expressions",
    "Length Requirements: \n Description: Specifying concrete limits on text length including the number of paragraphs, sentences, words, initial words in paragraphs, or length of each sentence in terms of words or characters. \n Example: \n - Number of Paragraphs \n - Number of Sentences \n - Number of Words \n - First Word in i-th Paragraph should be ... \n - Number of characters \n - Length of each sentence in terms of words or characters",
    "Content Structure: \n Description: Organizing content according to specific requirements, including the number of placeholders, inclusion of postscripts, presence of specific phrases or idioms, use of specific tags or markers, and the number of references or citations. \n Example: \n - Number of placeholders \n - Postscript \n - Specific phrases or idioms \n - Presence of specific tags or markers \n - Number of references or citations",
    "Case Constraints: \n Description: Imposing constraints on the use of upper or lower case letters in the text, including overall frequency, use of title case for headings, consistency within paragraphs, and consistency in the use of abbreviations or acronyms. \n Example: \n - Capital words or Lowercase words \n - Frequency of capital/lower words \n - Title case for headings \n - Case consistency within a paragraph \n - Consistency in the use of abbreviations or acronyms",
    "Formatting Rules: \n Description: Specifying concrete formatting requirements for the text, including multiple sections, the number of bullet lists, highlighted sections, the name of the title, and specific alignment (left, right, center). \n Example: \n - Multiple sections \n - Number of bullet lists \n - Number of highlighted sections \n - Name of the title \n - Specific alignment (left, right, center)",
    "Mixed Approaches: \n Description: Combining various methods in the text response, such as repeating user prompts before answering, providing multiple responses for a single prompt, writing from different perspectives, and integrating questions and answers in the response. \n Example: \n - Repeat the user prompts before answering the question \n - Give multiple responses for a single prompt \n - Use of different perspectives in the response \n - Integrating questions and answers in the response",
    "Punctuation Usage: \n Description: Imposing specific rules on the use of punctuation marks, such as avoiding commas or colons, using specific punctuation marks at certain positions, the frequency of semicolons or ellipses, and the use of exclamation marks or question marks. \n Example: \n - No use of comma/colons \n - Specific punctuation marks at certain positions \n - Frequency of semicolons or ellipses \n - Use of exclamation marks or question marks",
    "Opening and Closing Rules: \n Description: Specifying concrete requirements for the opening and closing of the text, such as starting or ending with specific words, punctuation, or quotations, including a famous quote, or beginning or ending with a summary statement. \n Example: \n - Start/end with specific words \n - Start/end with specific punctuation or quotation \n - Start/end with a famous quote \n - Start/end with a summary statement",
    "Literary Techniques: \n Description: Using specific literary techniques to enhance the text, including metaphors or similes, alliteration or assonance, hyperbole or understatement, irony or sarcasm, and personification or onomatopoeia. \n Example: \n - Use of metaphors or similes \n - Use of alliteration or assonance \n - Use of hyperbole or understatement \n - Use of irony or sarcasm \n - Use of personification or onomatopoeia",
    "Output Formatting: \n Description: Ensuring the text is output in a specified format, such as a table or list, using a specific font or color, in a specific file format (e.g., PDF, CSV), in a certain structure (e.g., JSON, XML), or in a particular layout (e.g., grid, list). \n Example: \n - Output in a specific format (e.g., table, list) \n - Output in a specific font or color \n - Output in a specific file format (e.g., PDF, CSV) \n - Output in a specific structure (e.g., JSON, XML) \n - Output in a specific layout (e.g., grid, list)",
    "Perspective Constraints: \n Description: Ensuring the text is written from a specific narrative perspective, such as strictly first-person, second-person, or third-person, alternating perspectives in different sections, using an omniscient or limited viewpoint, and avoiding shifts in perspective mid-paragraph. \n Example: \n - Write strictly from a first-person, second-person, or third-person perspective \n - Alternate perspectives in different sections \n - Use an omniscient or limited viewpoint \n - Avoid shifting perspectives mid-paragraph"
]


filter_format = '''
You are a linguistics expert. I will provide you with an original instruction and an revised instruction with added format constraints.
You need to extract the newly added constraints by comparing the original and new instructions, list them in the form of [Constraint N], and then determine if the original and new instructions meet the following conditions:

1. The revised instruction should contain all the content of the original instruction.
2. The constraints added on the new instruction should be reasonable should not conflict with each other.
3. The revised instruction should be a reasonable and meaningful question likely to be a real question a user might ask, and contain enough context for answering, and it should be an instruction rather than a statement.

The input format is:
[Original instruction]: Original instruction
[Revised Instruction]: Revised instruction with added format constraints

The output format is:
[Constraints Indentified]:
Constraint 1: Your first extracted constraint
Constraint 2: Your second extracted constraint
...
Constraint N: Your Nth extracted constraint
[Analysis]: Here, you need to analyze each condition one by one to see if they are met.
[Final Result]: Output YES or NO here. If all the 3 conditions are met you should output YES, otherwise output NO. Do not include any other information.

Here is an example for your reference:

[Original instruction]: Write a paragraph about the effect of climate change in the Baltic Sea.
[Revised Instruction]: Write a single paragraph of no more than 150 words discussing the effect of climate change on the Baltic Sea, ensuring that each sentence starts with a lowercase letter. The paragraph must include statistical data and utilize the keyword "hypothesis" once. The paragraph should begin with the phrase "As evidence mounts" and end with a question mark. Maintain a formal tone throughout the response.
[Constraints Indentified]:
Constraint 1: Write a single paragraph of no more than 150 words.
Constraint 2: Ensure that each sentence starts with a lowercase letter.
Constraint 3: Utilize the keyword 'hypothesis' once.
Constraint 4: Begin with the phrase 'As evidence mounts'.
Constraint 5: End with a question mark.
Constraint 6: Maintain a formal tone throughout the response.
Constraint 7: Include Statistical data.
[Analysis]: The revised instruction contains all the content of the original instruction, so the first condition is met. The constraint 2 and constraint 4 conflict with each other, as the phrase 'As evidence mounts' should start with a capital letter with is incompatible with the request that each sentence should start with a lowercase letter. So the second condition is not met. Since the second condition is not met, we have no need to further consider the third condition. The final result should be NO. 
[Final Result]: NO
---------------------------------------------------------------------------------------------------------------------------------

Now please evaluate the following original instruction and revised instruction and provide your judgment:
[Original instruction]: {}
[Revised Instruction]: {}
Please provide your judgment:
'''



follow_judger = '''
You are a linguistics expert. I will provide you with a instruction and a response to this instruction. I will also give your a list of constraints that the response should follow. Your task is to determine whether the response adheres to these constraints.

Please follow the input and output formats provided below:

### Input format:
[Instruction]: Provide a summary of the benefits of learning a second language in three bullet points. Each bullet point should be one sentence long and include the word "advantage." Avoid using technical jargon and ensure the summary is suitable for a general audience.  
[Response]: 
- One advantage of learning a second language is enhanced cognitive abilities.
- Another one is the increased cultural awareness and appreciation.
- A third advantage is the improved employment opportunities.
[Constraints]: ["The summary should be in three bullet points.", "Each bullet point should be one sentence long.", "Each bullet point should include the word 'advantage'.", "Avoid using technical jargon.", "Ensure the summary is suitable for a general audience."]

### Output format:
```json
{{
    "Analysis": {{
        "Constraint 1": "Constraint 1 is met, the response contains three bullet points.",
        "Constraint 2": "Constraint 2 is met, each bullet point is one sentence long.",
        "Constraint 3": "Constraint 3 is not met, the setence after the second bullet point does not include the word 'advantage'.",
        "Constraint 4": "Constraint 4 is met, the response avoids technical jargon.",
        "Constraint 5": "Constraint 5 is met, the summary is suitable for a general audience."
    }},
    "Final_result": [true, true, false, true, true]
}}
```
Note that the value of "Constraints_extracted" should be a dictionary containing the constraints extracted from the revised instruction and the value of "Final_result" should be a python list of boolean values indicating whether each constraint is met.

### Provide your judgment result below, Please note that you should only return a json object with the format we discussed above:

[Instruction]: {}  
[Response]: {}  
[Constraints]: {}
[Output]: 

'''


constraints_extractor = '''

You are a linguistics expert. I will provide you with an original instruction, and a revised instruction that includes additional constraints. Your task is to identify the constraints added in the revised instruction compared with the original instruction and determine which of these constraints relate to keywords, length, or changing case.

To be more specific:
    **Keyword Usage** may include requirements about the presence of specific keywords, the frequency of these keywords, and letter frequency in keywords. Note that only keywords with specific definitions or requirements are considered, instead of general keywords like transition phrase or third-person perspectives.
    **Length Requirements** may include limits on the number of words, number of characters, or the length of each sentence or the whole response.
    **Case Constraints** may involve requirements about the use of capital words or lowercase words in the prompt.
You also need to state why the constraints can be checked by pure Python code without searching for outside resources and assuming some certain prerequisites.

You should follow the input and output formats provided below:
### Input format:
**Original Instruction:** What is oyster sauce?
**Revised Instruction:** Describe oyster sauce, use only one-sentence responses, begin with \"Oyster sauce is\", and incorporate an idiomatic expression that illustrates its flavor profile and do not exceed 200 words. Do not use any contractions in your response.

### Output format: 
```json
{{
    "Constraints_extracted": {{
        "Constraint 1": "Use only one-sentence responses.",
        "Constraint 2": "Begin with "Oyster sauce is.",
        "Constraint 3": "Incorporate an idiomatic expression that illustrates its flavor profile.",
        "Constraint 4": "Do not exceed 200 words.",
        "Constraint 5": "Do not use any contractions."
    }},
    "Analysis": "Constraint 2 is related to keywords constraints and can be checked by python code using startwith() function. Constraint 4 is related to length constraints and can be checked by python code using len() and split() function to count how many words. Constraints 5 is related to keywords constraints but can not be checked by python code since the variety of contractions is too large.", 
    "Final_result": ["Constraint 2", "Constraint 4"]
}}
```
The value of "Constraints_extracted" should be a dictionary containing the constraints extracted from the revised instruction. The value of "Analysis" should be a string explaining which constraints relate to keywords, length, or changing case and why they can be checked by pure Python code. The value of "Final_result" should be a python list containing the constraints that relate to keywords, length, or changing case and can be checked by pure Python code.

### Provide your judgment result below, Please note that you should only return a json object with the format we discussed above:

**Original Instruction:** {original_instruction}  
**Revised Instruction:** {revised_instruction}  
**Output:**

'''



prompt_template = """
You are an expert for writing evaluation functions in Python to evaluate whether a response strictly follows a format constraints in the user instruction.

## Input Format:
- A format constraint in the user instruction.
## Output Format:
A single JSON includes the evaluation function in the key `func`, and a list of three test cases in the key `cases`, which includes an input in the key `input` and an expected output in the key `output` in (true, false).
Here is an example of output JSON format: {{"func": JSON_STR(use only \\n instead of \n), "cases": [{{"input": bool, "output": bool}}]}}.
## Other Requirements:
1. Please write a Python function named `evaluate` to evaluate whether an input string `response` follows this format constraint. If it follows, simply return True, otherwise return False. 
2. If your function requires any external libraries, ensure to include the import statements within the evaluate function.

Here is an example for you:
## Input: "Do not exceed 200 words"
## Output:
```json
{{
  "func": "def evaluate(response: str) -> bool:\\n    import re\\n    word_count = len(re.findall(r'\\b\\w+\\b', response))\\n    return word_count <= 200",
  "cases": [
    {{
      "input": "This is a test response with exactly one hundred and ninety-nine words. This response is designed to test the evaluation function to ensure that it correctly identifies responses that do not exceed two hundred words. The evaluation function will count the number of words in this response and return True if the count is two hundred or less. In this case, since the response has only one hundred and ninety-nine words, the function should return True. The evaluation function is written in Python and uses a regular expression to count the words. The regular expression looks for word boundaries and matches sequences of word characters. By counting the matches found by the regular expression, the function can determine the number of words in the response. If the word count is within the specified limit, the function returns True; otherwise, it returns False. This test case ensures that the function works correctly for responses that are within the limit. To ensure accuracy, it is important to test the function with various inputs, including those that are just below, at, and just above the word limit. This helps verify that the function correctly identifies responses that meet the constraint. The following test case will have exactly two hundred words to further test the function's accuracy.",
      "output": true
    }},
    {{
      "input": "This response is designed to exceed the two hundred word limit. It continues with more text to ensure that the evaluation function correctly identifies responses that are too long. By exceeding the limit, this response should cause the function to return False. The purpose of this test case is to verify that the function does not mistakenly allow responses that have more than two hundred words. To achieve this, the response includes additional sentences and phrases that push the word count beyond the specified limit. The evaluation function must accurately count the words and determine that this response is not within the acceptable range. By testing with this longer response, we can ensure that the function correctly handles cases where the input exceeds the word limit. This is crucial for maintaining the integrity of the constraint and ensuring that only responses that meet the requirements are accepted. The evaluation function's accuracy is tested by providing inputs that vary in length, ensuring comprehensive coverage of possible scenarios. This particular test case deliberately exceeds the word limit by including extra content, such as additional explanations and details, to thoroughly test the function's capability to identify responses that are too long. The final word count for this response is more than two hundred words, making it a valid test case.",
      "output": false
    }},
    {{
      "input": "This is a short response.",
      "output": true
    }}
  ]
}}
```

Here is the constraint: {}
Please output your json here:

"""
