<!-- Slide number: 1 -->

![](GoogleShape56p13.jpg)
# Markdown Quality Training
GameNightGpt

### Notes:

<!-- Slide number: 2 -->
# Preparation
Understanding the Game: Before editing your game manual, it’s paramount you understand the scope and if possible how to play the game. To ensure terminology and gameplay descriptions are accurate.
Study the game manual
Research about the game
You can watch youtube videos on how to play the game.

### Notes:

<!-- Slide number: 3 -->
# Content Scope
Define what is needed vs. what can be omitted
Keep: Every detail that teaches how to set up, play, and score the game.
Omit: Table of Contents, Index, Credits, Author’s Appreciation, and Overviews/Appendices (unless they contain specific rules).
Special Case: "Components" sections should usually be omitted, but you must check them for icon descriptions that appear nowhere else and also confirm if it doesn’t have explanations on how to play the game.

### Notes:

<!-- Slide number: 4 -->
# Structural Markdown & Formatting
Headers: You always start with a Level 2 header ‘##’ and it’s important you follow hierarchy.
Level 2 header ‘##’
Level 3 header ‘###’
Level 4 header ‘####’
Every header must include a page number (e.g., "## SETUP (Page 3)")
If a section appears under the wrong header visually in the PDF, move it to the logical correct header in markdown. (This happens rarely)

### Notes:

<!-- Slide number: 5 -->

![](GoogleShape79p17.jpg)

![](GoogleShape80p17.jpg)

### Notes:

<!-- Slide number: 6 -->

![](GoogleShape85p18.jpg)

### Notes:

<!-- Slide number: 7 -->
# Structural Markdown & Formatting (Cont’n)

Lists: Use specific syntax for unordered lists ("-") and ordered lists ("1." or "1)") while maintaining indentation.

![](GoogleShape94p19.jpg)

![](GoogleShape91p19.jpg)

![](GoogleShape95p19.jpg)

![](GoogleShape90p19.jpg)

### Notes:

<!-- Slide number: 8 -->
# Structural Markdown & Formatting (Cont’n)

Tables: When you come across a table that clearly shows rows and columns, this is how you should input it in the markdown.
	Header row: | Column 1 | Column 2 | Column 3 |
			      |---------------|--------------|---------------|
	First row:      | Details | Details | Details |
Second  row:| Details | Details | Details |
NOTE: Markdown tables must have a header row; if the original has none, leave the header cells empty.

### Notes:

<!-- Slide number: 9 -->

![](GoogleShape107p21.jpg)

![](GoogleShape106p21.jpg)

### Notes:

<!-- Slide number: 10 -->
# Structural Markdown & Formatting (Cont’n)

Text Styling:
Bold: Use double asterisks (**text**)
Italics: Use single asterisks (*text*) or underscores (_text_).
Bold Italics: Use triple asterisks (***text***).

### Notes:

<!-- Slide number: 11 -->
# Visual Descriptions (Images & Icons)
Image References:
All image descriptions must start with ‘>’.
Placement: Describe images at the top if they are on the left/above the text, and at the bottom if on the right/below.
In-line Steps: For complex diagrams with numbered steps, you can either describe the image all at once or describe the image progressively alongside the corresponding manual text rather than all at once(recommended)

### Notes:

<!-- Slide number: 12 -->

![](GoogleShape125p24.jpg)

![](GoogleShape124p24.jpg)

### Notes:

<!-- Slide number: 13 -->

![](GoogleShape131p25.jpg)

![](GoogleShape130p25.jpg)

### Notes:

<!-- Slide number: 14 -->

![](GoogleShape136p26.jpg)
> image showing detailed setup from the Revive board game, featuring a large main board on the right (1) divided into green, yellow, and brown regions with interconnected paths and symbols, a character board on the left (2) marked “Use the Sun side,” a group of futuristic cards forming the “Active area” (12) below the character board, a “Resting area” (6) on the right side holding a stack of cards, colored markers or player tokens (3) positioned near the top right, a mask-shaped faction token (7) and a resource or upgrade tile (8) beside it, a sun icon marker (9), a row of circular progress or score indicators (10) beneath the character board, and a power track (5) and additional markers (13) along the bottom edge, all presented in warm earthy tones of brown, yellow, and green with a futuristic, post-apocalyptic design aesthetic.

### Notes:

<!-- Slide number: 15 -->
# Visual Descriptions (Images & Icons) Cont’n

Icon Descriptions:
Format: Start with what it represents, followed by what it looks like (e.g., "Victory points (icon of a trophy cup)").
Consistency: If an icon meaning is known (e.g., "Victory Points"), use that meaning consistently. If the meaning is unknown, describe the visual (e.g., "trophy cup").
Handling Broken Text: Icons within sentences often break the text flow during conversion; they must manually fix jumbled words
Don’t spend too much time trying to describe super-complex images. Your image descriptions just need to provide information that is not available elsewhere in the text of the manual on how to set up, play, and score the game. If the image doesn’t explain how to set up, play, and score the game, you can skip the image.
Description Scope: Focus only on information needed to setup, play, or score. Purely decorative images can be skipped.

### Notes:

<!-- Slide number: 16 -->
# Visual Descriptions (Images & Icons) Cont’n

Icons Within Sentences
If an icon appears within a line of text, describe it briefly in parentheses right after it appears.Example: “Take each of your Players to the Game store (Icon representation of a store – icon takes the shape of a small sack) and take two coin tokens from it.
If an icon appears within a line of text, but the icon name wasn’t mentioned, meaning the icon was used instead of a word, or to complete a sentence. Use the correct word for it, then describe its appearance briefly in parentheses right after the correct word.

### Notes:

<!-- Slide number: 17 -->

![](GoogleShape155p29.jpg)
The right way to write it in the markdown file:
“The Councilor with the most victory points (icon of a trophy cup) is the winner. If the Cult has the most victory points (icon of a trophy cup), then the player who is the current Cult Conspirator is the winner instead.”
NOTE:
You don’t need to include the visual description (icon of a trophy cup) if it repeats multiple times over and over in the manual. Use the icon meaning “victory points” is used consistently everywhere, and the visual description appears at least once, “(icon of a trophy cup)”.
You have to use the icon's meaning everywhere when describing the icon.

### Notes:

<!-- Slide number: 18 -->
# Quality Control & Tools

Checklist for reviewing the markdown file before final submission:
All headers and lists use correct markdown syntax.
Headers should have the page number where it is located. Example: (## SETUP (page 2))
Image descriptions are accurate and formatted with >.
No missing sections or misplaced text due to column mixing.
In-text icon descriptions should be formatted with ().
In-text icon descriptions should have a name for the description inside the parentheses. E.g. fire (flame icon)
File reads clearly and matches the manual’s order.

### Notes:

<!-- Slide number: 19 -->
# Quality Control & Tools Cont’n
Ensure the final output is error-free and ready for submission.
Recommended Tools:
If you are editing in Github: Download “Grammerly” extension in your browser to catch typos.
If you are editing in VS-CODE: Download “Code Spell Checker” extension to catch typos.
NOTE: Don’t correct what you think is a typo from the manual, just use what is in the manual, only correct the texts you added yourself when describing images/icons or broken texts due to conversion process.

### Notes:

<!-- Slide number: 20 -->
# For more Studies and Understanding
Click the link to the detailed guideline for better understanding.

https://docs.google.com/document/d/1OYJDWfT7JOlm0UX6iJn89B-t9ly8FKQvYTzHDsZ4W88/edit?tab=t.0#heading=h.gsi5ddy0mxbd

### Notes: