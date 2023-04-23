# minimal_auto_gpt
a minimal implement for Chain of Thought and command generator

### test run 1:

```
RESPONSE: {"thought": "To complete the task, I need to search for information related to iPhone 14.", "command": {"name": "search", "args": ["iPhone 14"]}}
command: {'name': 'search', 'args': ['iPhone 14']}
press enter to continue...EXEC RESULT: {'results': '[{variable_2741632f}, {variable_2935c7d7}, {variable_6471ca9e}, {variable_e2a9edc5}, {variable_f41b74ed}]'}
RESPONSE: {"thought": "I got search results, I'll save them into a variable and summarize the information.", "command": {"name": "llm", "args": ["summarize the information about iPhone 14 from {variable_2741632f}, {variable_2935c7d7}, {variable_6471ca9e}, {variable_e2a9edc5}, and {variable_f41b74ed}"]}}
command: {'name': 'llm', 'args': ['summarize the information about iPhone 14 from {variable_2741632f}, {variable_2935c7d7}, {variable_6471ca9e}, {variable_e2a9edc5}, and {variable_f41b74ed}']}
press enter to continue...EXEC RESULT: {'results': '{variable_c9e7315d}'}
RESPONSE: {"thought": "Now that I have a summary of the information, I'll save it into a file for later reference.", "command": {"name": "write_file", "args": ["iPhone14_summary.txt", "{variable_c9e7315d}"]}}
command: {'name': 'write_file', 'args': ['iPhone14_summary.txt', '{variable_c9e7315d}']}
press enter to continue...EXEC RESULT: {'results': 'success write to iPhone14_summary.txt'}
RESPONSE: {"thought": "Next, I'll search for specific details about the iPhone 14 camera from the summary file.", "command": {"name": "search_file", "args": ["iPhone14_summary.txt", "camera of iPhone 14\\b"]}}
command: {'name': 'search_file', 'args': ['iPhone14_summary.txt', 'camera of iPhone 14\\b']}
press enter to continue...EXEC RESULT: {'results': '[{variable_a49fed48}, {variable_14636ded}]'}
RESPONSE: {"thought": "I found some information on the iPhone 14 camera. I'll use llm to generate a detailed description.", "command": {"name": "llm", "args": ["generate a detailed description of the iPhone 14 camera based on {variable_a49fed48} and {variable_14636ded}"]}}
command: {'name': 'llm', 'args': ['generate a detailed description of the iPhone 14 camera based on {variable_a49fed48} and {variable_14636ded}']}
press enter to continue...EXEC RESULT: {'results': '{variable_16ace900}'}
retry 1: for exception 'choices'
RESPONSE: {"thought": "I have a detailed description of the iPhone 14 camera. I'll save it into a variable for future use.", "command": {"name": "save_variable", "args": ["iPhone14_camera_description", "{variable_16ace900}"]}}
command: {'name': 'save_variable', 'args': ['iPhone14_camera_description', '{variable_16ace900}']}
press enter to continue...EXEC RESULT: {'results': '{iPhone14_camera_description}'}
RESPONSE: {"thought": "To finish the task, I need to write a document about the iPhone 14. I'll use llm to generate an outline and fill in the details from the information I gathered.", "command": {"name": "llm", "args": ["generate an outline for an iPhone 14 document and fill it in with information from {variable_c9e7315d} and {iPhone14_camera_description}"]}}
command: {'name': 'llm', 'args': ['generate an outline for an iPhone 14 document and fill it in with information from {variable_c9e7315d} and {iPhone14_camera_description}']}
press enter to continue...EXEC RESULT: {'results': '{variable_7905251f}'}
RESPONSE: {"thought": "I got the outline of the document. I'll save it into a variable, then write it into a file.", "command": {"name": "save_variable", "args": ["iPhone14_document_outline", "{variable_7905251f}"]}}
command: {'name': 'save_variable', 'args': ['iPhone14_document_outline', '{variable_7905251f}']}
press enter to continue...EXEC RESULT: {'results': '{iPhone14_document_outline}'}
RESPONSE: {"thought": "I'll save the iPhone 14 document outline into a file for later use.", "command": {"name": "write_file", "args": ["iPhone14_document_outline.txt", "{iPhone14_document_outline}"]}}
command: {'name': 'write_file', 'args': ['iPhone14_document_outline.txt', '{iPhone14_document_outline}']}
press enter to continue...EXEC RESULT: {'results': 'success write to iPhone14_document_outline.txt'}
RESPONSE: {"thought": "I have completed the task. I'll call the stop command now.", "command": {"name": "stop", "args": []}}
job done...
```
