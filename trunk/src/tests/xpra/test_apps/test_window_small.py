#!/usr/bin/env python

import gtk

width = 50
height = 10

def make_win(min_width=-1, min_height=-1, max_width=-1, max_height=-1):
	window = gtk.Window(gtk.WINDOW_TOPLEVEL)
	window.set_title("min=%s - max=%s" % ((min_width, min_height), (max_width, max_height)))
	#window.set_size_request(width, height)
	window.connect("delete_event", gtk.mainquit)
	window.set_geometry_hints(window,
							min_width=min_width, min_height=min_height,
							max_width=max_width, max_height=max_height,
							base_width=100, base_height=100,
							width_inc=8, height_inc=8,
							#min_aspect=1, max_aspect=1,
							)
	window.show_all()

def main():
	make_win(width, height, width, height)
	gtk.main()


if __name__ == "__main__":
	main()