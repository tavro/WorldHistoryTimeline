import sys
import os


special_chars = ['—', '-', '"', ',', '\'', ':']


def open_file(path):
	file = open(path, 'r')
	content = file.read()
	lines = content.split('\n')
	compile(lines)


def create_file(content):
	filename = sys.argv[1].split('.')[0] + '.html'
	path = '../' + filename
	file_exists = os.path.exists(path)
	if file_exists:
		with open(path, 'r+') as f:
			f.truncate(0)
	file = open(path, "a")
	for line in content:
		file.write(line + '\n')
	file.close()
	file = open(path, "r")
	print(file.read())


def compile(lines):
	result = []
	result.append('<span>')
	for line in lines:
		compiled_line = handle_line(line)
		result.append('\t' + compiled_line)
	result.pop()
	result.append('</span>')
	create_file(result)


def handle_line(line):
	if line:
		if all(char.isalpha() or char.isdigit() or char.isspace() or char in special_chars for char in line):
			return line
		elif line[0] == '.':
			line = line[1:]
			strs = line.split()
			class_name = strs[0]
			rest = ''
			for str in strs[1:]:
				rest += ' '
				rest += str
			return '<p class="' + class_name + '">' +  rest + '</p>'
		elif line[0] == '#':
			size = line[1]
			header = '<h' + size + '>'
			closing = '</h' + size + '>'
			if '@' in line:
				link = handle_line(line[3:])
				return header + link + closing
			return header + closing
		elif line[0] == '@':
			line = line[1:]
			words = line.split()
			return '<a href="' + words[0] + '">' + words[1] + '</a>'
	match line:
		case '[':
			return '<div>'
		case ']':
			return '</div>'
		case '':
			return '<br>'


if __name__ == '__main__':
	open_file(sys.argv[1])
