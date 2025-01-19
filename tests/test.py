import re

# Define the pattern
pattern = re.compile(r"(?:\[(.*?)\] )?(.*?): (.*)")

# Example chat log (contains \u200e character)
chat_log = """
[06.01.25, 22:13:55] Sarp Onkahraman: 8:45 right
[07.01.25, 08:55:30] Sarp Onkahraman: Running a bit late
[07.01.25, 08:55:35] Sarp Onkahraman: You there
[07.01.25, 08:55:47] Max 🔨: yes
[11.01.25, 18:41:00] Sarp Onkahraman: Hey guys hows it goin
[11.01.25, 18:48:30] Max 🔨: if you want to join, christos and i are going to meet in like 20min. We are going to meet for like 2 hours to do project. We did a lot of things over the last two days✌🏼 maybe we can show you
\u200e[11.01.25, 18:50:24] Sarp Onkahraman: \u200eaudio omitted
[11.01.25, 19:14:24] Max 🔨: alr have fun with your fam🤞🏼
we will work on it together every day so if you find time let us know 😊
[11.01.25, 19:33:22] Sarp Onkahraman: Thank you guys
[11.01.25, 19:34:07] Sarp Onkahraman: But I also dont want leave you alone with the project
[11.01.25, 19:34:35] Sarp Onkahraman: Maybe tomorrow we meet online and distribute some work
[11.01.25, 19:34:54] Sarp Onkahraman: Otherwise would be unfair
[11.01.25, 19:35:57] Max 🔨: there is not much to distribute
[11.01.25, 19:36:05] Max 🔨: we sit together and debug
"""

# Remove problematic characters (e.g., \u200e) from the chat log
cleaned_chat_log = re.sub(r"[\u200e]", "", chat_log)

# Find all matches in the cleaned chat log
matches = pattern.findall(cleaned_chat_log)

# Extract names from the second capturing group
names = [match[1] for match in matches]

# Remove duplicates by converting to a set
unique_names = set(names)

# Display results
print("Extracted Names:", unique_names)
