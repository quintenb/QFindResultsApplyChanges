# coding=utf8
import sublime, sublime_plugin
import re, os

debug = False

class Save2Command(sublime_plugin.WindowCommand):

	def run(self):
		window = sublime.active_window()
		view = window.active_view()
		if window and view and 'Find Results.hidden-tmLanguage' in view.settings().get('syntax'):
			view.run_command('find_results_apply_changes')
		else:
			view.run_command('save')

class FindResultsApplyChangesCommand(sublime_plugin.TextCommand):

	def run(self, edit):

		if sublime.active_window().active_view().name() == 'Find Results':
			v = sublime.active_window().active_view()

		# avoid corruption

			if v.settings().get('FindResultsApplyChanges-possible-corruption', False):
				sublime.message_dialog('Committing twice when new newlines has been inserted will corrupt the file. Skipping commit.')
				return

		# set 'Find results' regions

			if debug:
				draw = sublime.DRAW_OUTLINED
			else:
				draw = sublime.HIDDEN
			region_lines  = v.find_all(r'^ +([0-9]+)(\: |  )')
			v.erase_regions('FindResultsApplyChanges-lines')
			v.add_regions('FindResultsApplyChanges-lines', region_lines, 'entity.name.function', '', draw)

			region_files  = v.find_all(r'^\n[^\n]+\:\n')
			v.erase_regions('FindResultsApplyChanges-files')
			v.add_regions('FindResultsApplyChanges-files', region_files, 'entity.class.name', '', draw)

		# get 'Find Results' regions

			region_files = v.get_regions('FindResultsApplyChanges-files')
			region_lines = v.get_regions('FindResultsApplyChanges-lines')

			changes = {}

			for file in range(len(region_files)):

				region_file = region_files[file]
				try:
					next_region_file = region_files[file+1]
				except:
					next_region_file = sublime.Region(v.size(), v.size())
				file_name = re.sub(r'\:$', '', v.substr(region_file).strip())

				if debug:
					print(file_name);

				changes[file_name] = {}

				for line in range(len(region_lines)):

					region_line = region_lines[line]
					try:
						next_region_line = region_lines[line+1]
					except:
						next_region_line = sublime.Region(v.size(), v.size())

					if region_line.a > region_file.a and region_line.a < next_region_file.a:
						line_number = int(re.sub(r'\:$', '', v.substr(region_line).strip()))-1
						line_content = v.substr(sublime.Region(region_line.b, (next_region_line.a if next_region_line.a < next_region_file.a else next_region_file.a)-1))
						line_content =  re.sub(r'\n +\.+$', '', line_content) # remove 'dots' Ellipsis
						changes[file_name][line_number] = line_content

			if debug:
				print(changes)

			# remove footer
			if changes[file_name]:
				footer_line = max(changes[file_name].keys())
				changes[file_name][footer_line] = re.sub(r'\n\n[0-9]+ matche?s? (across|in) [0-9]+ files?$', '', changes[file_name][footer_line])

		# apply changes

			for f in changes:
				f = f.strip();
				if f and changes[f] and os.path.exists(f):
					content = self.read(f).split('\n');
					modified = False
					for k in changes[f].keys():
						k = int(k)
						if content[k] != changes[f][k]:
							content[k] = changes[f][k]
							if debug:
								print('Line number: '+str(k+1))
								print('Has new value: '+changes[f][k]);
							if '\n' in changes[f][k]:
								v.settings().set('FindResultsApplyChanges-possible-corruption', True);

							modified = True
					if modified:
						print('Writing new content to file '+f)
						self.write(f, '\n'.join(content))

	def is_enabled(self):
		return sublime.active_window().active_view() and sublime.active_window().active_view().name() == 'Find Results'

	def read(self, f):
		return open(f, 'r', newline='').read()

	def write(self, f, c):
		open(f, 'w+', encoding='utf-8', newline='').write(c.encode('utf-8'))
