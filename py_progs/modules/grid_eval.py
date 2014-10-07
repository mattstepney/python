#!/usr/bin/env python 

'''
                    Space Telescope Science Institute


Synopsis:   grid_eval is a package of python routines intended to
	aid in the understanding how models in a grid vary.  
	
	Some of the routines run the c routine py_compare which 
	compares two spectra produced by python.  This routine 
	gets inpt from a .pf file.  The usual progression
	of steps is as follows:

	pf2ls -- to create a .ls file from a collection of .pf files
	make_runfile -- to create a file which contains all the 
		various combinations of py_compare that need to
		be run
	run_self_compare -- to actually run all the comparisions.
		This can take a long time to run on a large grid
	analyze -- to read the output file from run_self_compare
		and summarize how everything varied
	
	Note that there are certain applications where the pfs2ls
		routine is useful from a standalone sense.
		

Notes:
	This version does not use sqlite

	Instead it has it's own concept of a table which is a list.  
	Each row in the list consists of a bunch of name, value pairs

	The tables are specific for use with python since the first
	two columns are the rootname and the spectrum number.  Usually
	operations preserve these two columns regardless of what else
	happens

Problems:

	Bacause it is just one routine the subsidiary routines show
	up in help.

	There are a number of extra subroutines that appear to be
	for there for test purposes which are confusing.

History:

	090404	Bagan with the current version of carlo.py
	090420	Removed the sqlite portions of the test routine
		so I could actually make progress
	090829	Tried to undersdand what I had intended

'''

import sys
import os
import glob
import numpy
import math
import datetime


# These are the global variables
python_version='unknown'
current_inclination=0.0


# Next few routines are general purpose utilities

def get_filenames(dirname='.',descriptor='*.pf'):
	'''
	get_filename(dirname,descriptor) locates and returns all 
	the filenames of the type specified by descriptor
	'''
	searchlist=dirname+'/'+descriptor
	print searchlist

	names=glob.glob(searchlist)


	if len(names)==0:
		print 'Error: get_filenames: No files with this searchlist: %s ' % searchlist
	return names

def split_filename(name='test/test/foo.dat'):
	'''
	split a filename into a path, filename, a rootname, and an extension.

	In short get every possible thing one could want to know about a filename
	(except of course whether it exists)


	'''

	try:
		i=name.rindex('/')
		dirname=name[0:i+1]
		name=name[i+1:len(name)]
	except ValueError:
		dirname='./'
	
	try:
		i=name.rindex('.')
		root=name[0:i]
		ext=name[i:len(name)]
	except ValueError:
		root=name
		ext=''
	return dirname,name,root,ext
	

# Next routines cover the reading and writing of ls files including the 
# createion of ls files from pf files.  The main interface is the "table" 

def read_pf(filename='test'):
	'''
	read and parse a parameter file.  Note that
	this routine can handle the extension or not,
	but it will always try to read the .pf file

	This routine has been specifically written 
	to for python, the radiative transfer program

	A record is returned for each angle of of a python model, 
	and the  root of the filename is encoded into returned records.   

	The purpose of this is to make it possible to
	treat the angles as variables, even though
	they are calculated in the same grid.

	It DOES NOT handle the type of records needed
	for gen_grid.py

	090403	ksl	Made this modification
	'''

	# Check whether .pf has been added
	try:
		n=filename.rindex('.')
		name=filename[0:n]+'.pf'
		root=filename[0:n]
	except ValueError:
		name=filename+'.pf'
		root=filename

	x=[]
	nangles=0
	angles=[]
	phases=[]


	f=open(name,'r')
	lines=f.readlines()
	f.close()
	i=0
	while i<len(lines):
		q=lines[i].strip()
		if q[0]!='#' and len(q)>1:
			q=q.split()
			words=q[0].split('(')
			try:
				value=eval(q[1])
			except NameError:
				value=q[1]
			if words[0]=='no_observers':
				nangles=value
			elif words[0]=='angle':
				angles=angles+[value]
			elif words[0]=='phase':
				phases=phases+[value]
			else:
				# The next 2 lines are  needed for sqlite, and was deleted from
				# this version.  It is needed there because
				# Because it treats . as a special character
				# keyword=words[0].replace('.','_')
				# x=x+[[keyword,value]]

				x=x+[[words[0],value]]
		i=i+1
	
	if len(angles)!=nangles:
		print 'Error: %d observers but only %d angles' % (nangles,len(angles))
	if len(phases)!=nangles:
		print 'Error: %d observers but only %d phases' % (nangles,len(phases))

	# This section is to handle non python .pf files 
	if nangles==0:
		# print 'nangles ',nangles
		xx==[['filename',root],['nspec',-1]]+x
		return xx

	# This section is to handle python .pf files with multiple angles
	xx=[]
	i=0
	while i<nangles:
		zz=[['filename',root],['nspec',i+1]]+x+[['angle',angles[i]]]
		xx=xx+ [zz]
		i=i+1
	# print 'nangles ',nangles
	return xx

def pfs2table(filelist):
	'''
	Make the main table containing all of the pf files in a list. 
	
	filelist should be a list of names, e.g ['test1', 'test2' of
	parameter file names.  This routine reads all of the parameter
	files in a list and returns them as a single list

	090405	ksl	Modified to make sure multiple rows from read_pf
			do not increase the dimensionality of the list
	'''
	table=[]
	i=0
	while i<len(filelist):
		print filelist[i]
		table=table+read_pf(filelist[i])
		i=i+1
	return table



def pfs2ls(root='mdot',listroot='test'):
	'''
	pfs2ls creates a version of the .ls file by reading parameter files
	'''
	
	dirname='.'
	pfiles=root+'*.pf'
	filelist=get_filenames(dirname,pfiles)

	# This makes a table in which one row of the list corresponds to one spectrum in the
	# list.  The format of the rows is filename nspec and then all the variables
	table=pfs2table(filelist)
	print table[0]
	print '\n\n'
	print '\n\n'

	# Next line gets the unique choices in the table
	unique=table_get_choices(table)

	g=open(listroot+'.ls','w')
	for one in unique:
		print 'one variable', one
		string='#  VAR  %15s list '% one[0]
		i=1
		while i<len(one):
			string=string+' %8.3g' % one[i]
			if i%5==0 or i+1==len(one):
				print string
				g.write('%s\n' % string)
				string='#  VAR  %15s more '% one[0]

			i=i+1
		print 'xxxx ',i
		# if i%5 > 1:
		# 	print string
		# 	g.write('%s\n' % string)

	values=table_reduce(table)  # Eliminate all the columns which do not vary
	i=0
	while i< len(table):
		row=table[i]
		value=values[i]
	 	# print row[0],row[1],values[i]
		string='%-10s %5d ' % (row[0][1],row[1][1])
		j=0
		while j<len(value):
			try:
				string=string+' %8.3g' % value[j][1]
			except TypeError:
				print 'Error: TyepError in pf2ls ',value,string
			j=j+1
		# print string
		g.write('%s\n' % string)
		i=i+1
	g.close()

def ls2table(listfile):
	'''
	Make the main table from a list file

	090601	ksl	Added so that one could work with list files
			which is where we really want to store the variables
	'''
	# Check whether .ls has been added
	try:
		n=listfile.rindex('.')
		name=listfile[0:n]+'.ls'
		root=listfile[0:n]
	except ValueError:
		name=listfile+'.ls'
		root=listfile
	
	try:
		f=open(listfile,'r')
		lines=f.readlines()
		f.close()
	except IOError:
		print 'Error: ls2table: file %s does not exist' % listfile
		return []
		
	table=[]
	var_names=['filename','nspec']  # This is peculiar to python models
	for line in lines:
		# print line
		xline=line.strip()
		xline=xline.split()
		# print xline
		if xline[0]=='#':
			if xline[1]=='VAR' and xline[3]!='more':
				var_names=var_names+[xline[2]]
		else:
			record=[[var_names[0],xline[0]]]
			i=1
			while i<len(xline):
				try:
					record=record+[[var_names[i],eval(xline[i])]]
				except IndexError:
					print i,var_names,xline
			
				i=i+1
			table=table+[record]
	
	return table


# The next routiens have to do with the manipulation of tables
# This could be replaced with sqlite
	

def table_variable_column_names(table,colstart=2):
	'''
	Find which column names have values which vary in a table, starting
	with colstart. 

	identifying colstart is simply a way to avoid the filename and spectrum number
	in situatious specific to tables create from .pf files
	'''

	unique=[]
	
	i=colstart
	while i<len(table[0]):
		j=0
		values=[]
		while j<len(table):
			record=table[j]
			values=values+[record[i][1]]
			j=j+1
		v=numpy.unique(values)
		if len(v)>1:
			unique=unique+[record[i][0]]

		i=i+1
	
	return unique





def table_get_choices(table,colstart=2):
	'''
	get_choices determine what variables are changed in the table.  
	and values of the variables.

	Note: There is no guarantee that all possible combinations exist,
	since typically a complete grid would contain some non-physical
	choices, such as a mass lost rate exceeding the disk accretion 
	rate

	Note: The values are sorted

	090405	ksl	Modified to not worry about first two columns, which 
			now contain the filename (or root of it), and 
			a column (for a spectrum
	'''

	unique=[]
	
	i=colstart
	while i<len(table[0]):
		j=0
		values=[]
		while j<len(table):
			record=table[j]
			values=values+[record[i][1]]
			j=j+1
		values.sort()
		v=[record[i][0],values[0]]
		j=1
		while j<len(values):
			if v[len(v)-1]!=values[j]:
				v=v+[values[j]]
			j=j+1
		if len(v)>2:
			unique=unique+[v]

		i=i+1
	
	return unique



def table_select_rows(table,select=[['angle',30]]):
	'''
	table_select_rows returns those portions of a table which have the values set 
	by select.  Note that the select list need not return single values

	If no rows satisfiying the allowed conditions are found then an empty list
	will be returned

	This could easily be expanded to limits if that were desirable.

	090603 - Added logic and code to limit how closely numbers needed to agree with one 
		another to try to handle roundoff errors.  It is a little unclear that shis
		was necessary.
	'''

	i=0
	tmp_table=table
	while i<len(select):
		new_table=[]

		# locate the column to compare in the table
		desired=select[i]
		col=2
		while col<len(table[0]):
			name_value=table[0][col]
			if desired[0]==name_value[0]:
				break

			col=col+1
		if col==len(table[0]):
			print 'Error: col %s not found' % desired[0]
			return []

		# At this point I have found the column I want to compare, which 
		# was done just on the first row.  Now, I have to lopp though
		# the tmp table to get additional values
		# Now compare the values
		j=0
		while j<len(tmp_table):
			name_value=tmp_table[j][col]  # This is a name value pair

			try:
				delta=math.fabs(desired[1]-name_value[1])
				if delta == 0.0:
					# print 'xxxcheck', new_table
					new_table.append(tmp_table[j])
					#OLD new_table=new_table+[tmp_table[j]]
				else:   # Do a more detailed check
					denom=math.fabs(desired[1])+math.fabs(name_value[1])
					if delta < 1e-4 * denom:
						new_table.append(tmp_table[j])
						#OLD new_table=new_table+[tmp_table[j]]
			except TypeError: # It is presumably a string
				if desired[1]==name_value[1]:
					break
			# if desired[1]==name_value[1]:
			# 	new_table=new_table+[tmp_table[j]]

			j=j+1
		# if len(new_table)==0:
	 	#	print 'problem ', desired
		tmp_table=new_table

		i=i+1  # iterate on the next element in the select table
	return new_table


def table_select_columns(table,cols=['angle','wind.mdot']):
	'''
	table select columns reduces a table to the first two columns plus the 
	selected columns.  

	The new table will have the same number of rows as previously
	'''
	i=0
	new_table=[]
	while i<len(table):
		record=table[i]
		new_record=[]
		j=0
		while j<len(record):
			k=0
			while k<len(cols):
				if record[j][0]==cols[k]:
					new_record=new_record+[record[j]]
				k=k+1
			j=j+1

		new_table=new_table+[new_record]
		i=i+1
	return new_table

def table_reduce(table):
	'''
	table_reduce returns a new table, which eliminates all of the columns
	in the table which do not vary

	Note that this does not return either the filename or spectrum number
	'''
	variable_column_names=table_variable_column_names(table)
	newtable=table_select_columns(table,variable_column_names)
	return newtable


def table_update_column(table,colname,values=[1]):
	'''
	update the value or values in a column in
	a table, given a column name and and a
	list of values.  If len of values is 1,
	then replace all of the values in the column
	with the value.  If len>1 replace them one by
	one

	'''
	new_table=[]
	i=0
	n_updates=0
	while i < len(table):
		row=table[i]
		new_row=[]
		for x in row:
			if x[0]==colname:
				if len(values)==1:
					new_row=new_row+[[colname,values[0]]]
				else:
					new_row=new_row+[[colname,values[i]]]
				n_updates=n_updates+1
			else:
				new_row=new_row+[x]
		new_table=new_table+[new_row]
		i=i+1

	if n_updates<len(table):
		print 'Error: Only %d of %d rows updated' % (n_updates,len(table))

	return new_table
	

def table_make_combinations(table):
	'''
	table_make_combinations takes a list that contains multiple choices
	and expands it to produce a new table with more rows, and with
	only one choice for each variable in the original table 
	table.  That is a table containing

	[[var1,1,2]] --> [[var1,1],[var1,2]]


	'''
	newtable=[]
	xtable=table[0]
	k=1
	while k<len(xtable):
		newtable=newtable+[[xtable[0],xtable[k]]]
		k=k+1
	# So now we have indivdual lines for the first row	

	print newtable

	i=1
	while i<len(table):
		oldtable=newtable
		newtable=[]
		xtable=table[i]
		j=0
		while j<len(oldtable):
			k=1
			oldrow=oldtable[j]
			while k<len(xtable):
				newrow=oldrow+[xtable[0],xtable[k]]
				newtable=newtable+[newrow]
				k=k+1
			j=j+1
		i=i+1
	return newtable

# End of section of pure table manipulation utilities
# Beginning of section to identify comparisons that need to be made to
# do comparisons

# Next section is unused and should probably be deleted

def locate_delta(unique,variable='wind.mdot',value=1.6237767391899999e-10):
	'''
	locate_delta determines parameter values for possible models that can
	be compared to understand how changes in 'variable' at a specifc value

	This routine essentially assumes that models exist for every point
	in the parameter space, which must be checked separately
	'''

	# Get the variables that vary ignoring the rootname and the spectrum
	# number
	# unique=compare_pfs()

	primary=[]
	secondary=[]

	# identify the primary and secondary variables
	# The primary varialble is the one we are interested in at this time
	ok='no'
	nvar=0
	while nvar<len(unique):
		if variable==unique[nvar][0]:
			primary=unique[nvar]
			ok='yes'
		else:
			secondary=secondary+[unique[nvar]]
		nvar=nvar+1

	if ok=='no':
		print 'Failed to find ',variable
		return 
	
	print 'primary',primary

	# Within the primary variables next higher 'up' value
	# and the next lower 'down' value

	# Seems like this could be done quicker with sort



	delta=1e32
	i=1
	nbest=-99
	up=-99
	down=-99
	while i<len(primary):
		diff=math.fabs(primary[i]-value)
		if diff<delta:
			nbest=i
			delta=diff
		i=i+1


	print 'nbest',nbest
	up=primary[nbest+1]
	down=primary[nbest-1]
	print variable,down,value,up
	# Return the primary and secondary variables
	s=[variable,down,value,up]

	print 'Results of s - This is broken'
	print s
	print 'Finished s'


	return s,secondary

def do_one(variable='wind.mdot',value=1.6237767391899999e-10):
	'''
	This routine gets all of the ways to calculated deltas for a specific variable and mdot

	THIS is clearly a test, because there is no way to dfined what files one is searching
	'''

	# get the .pf files in this directory
	filelist=get_filenames()

	# Raed the pf files and make a table of them
	table=pfs2table(filelist)

	# Get the possilbe choices of items to vary
	unique=table_get_choices(table)

	print unique

	# Based on the variable input and the value, locate
	# all the possible of interest
	s,secondary=locate_delta(unique,variable,value)

	# Expand the combinations to individual choices
	x=table_make_combinations(secondary)
	print 'results of get combinations', x

	print 'finished printing results'
	i=0

	xxxx=[]
	# Construct the triplets of models to get
	while i<len(x):
		row=[[s[0],s[1]]]+[x[i]]

		xxx=[[variable,value],['none',-1],['none',-1],['none',-1]]

		z1=table_select_rows(table,select=row)
		if len(z1)>0:
			xxx[1]=[z1[0][0],z1[0][1]]

		row=[[s[0],s[2]]]+[x[i]]
		z2=table_select_rows(table,select=row)
		if len(z2)>0:
			xxx[2]=[z2[0][0],z2[0][1]]


		row=[[s[0],s[3]]]+[x[i]]
		z3=table_select_rows(table,select=row)
		if len(z3)>0:
			xxx[3]=[z3[0][0],z3[0][1]]

		# print 'z1',z1
		# print 'z2',z2
		# print 'z3',z3

		print 'xxx', xxx

		xxxx=xxxx+[xxx]


		i=i+1
	return xxxx

def generate_one(outfile='compare.in',variable='wind.mdot',value=1.6237767391899999e-10):
	'''
	This actually writes out what we want to a file

	090531 --- This looks like a test, because do_one is a test
	'''
	answer=do_one(variable,value)
	f=open(outfile,'w')
	i=0
	while i<len(answer):
		row=answer[i]
		print row
		if row[1][0]!='none' and row[2][0]!='none':
			f.write('%s  %d %s %d \n' % (row[1][0][1],row[1][1][1],row[2][0][1],row[2][1][1]))
		if row[2][0]!='none' and row[3][0]!='none':
			f.write('%s  %d %s %d \n' % (row[2][0][1],row[2][1][1],row[3][0][1],row[3][1][1]))
		i=i+1
	f.close()

# end of section to be deleted

# Next section is for handling the actual comparisons

def make_runfile(listfile='test.ls',outfile='test.run'):
	'''
	Construct all of the comparisons to be made and write them to a file
	'''

	# Get the main table
	table=ls2table(listfile)
	# Get the possilble choices of items to vary
	unique=table_get_choices(table)


	print 'Unique ',unique

	g=open(outfile,'w')

	for one in unique:
		print '# XVAR  %s ' % one[0]
		g.write('# XVAR  %s \n' % one[0])
		print 'one ',one
		i=1  # This is specific to python
		while i<len(one)-1:
			print '# DVAR %30s  %8.3g  %8.3g' %  (one[0],one[i],one[i+1])
			g.write('# DVAR %30s  %8.3g  %8.3g \n' %  (one[0],one[i],one[i+1]))
			# get all of the rows with values for the first value
			select_one=[[one[0],one[i]]]
			table_one=table_select_rows(table,select_one)

			# get all of the rows that have the value of upper value
			select_one=[[one[0],one[i+1]]]
			table_two=table_select_rows(table,select_one)
			# Create a new table from table one but with the variable of interest updated to the value we want
			# Except for the name and spectrum number this will be the values for which we are searching

			tmp_table=table_update_column(table_one,one[0],[one[i+1]])
			j=0
			while j<len(table_one):
				first_model=table_one[j]	
				tmp_row=tmp_table[j]
				# print 'Find',tmp_row
				select_one=tmp_row[2:len(tmp_row)] # This has all the values we are looking for
				# print 'find ',select_one
				# We now search table_two for a matching record
				x=table_select_rows(table_two,select_one)
				if len(x)>0:
					second_model=x[0]
					g.write('%-10s	%5d %-10s %5d\n' % (first_model[0][1],first_model[1][1],second_model[0][1],second_model[1][1]))
				# else:
				# 	print 'No model for ',select_one
				if j%1000 == 1:
					print 'Processed record %5d of table1 %5d from table2 %5d' % (j,len(table_one),len(table_two))
				j=j+1
			i=i+1


#  Next section actually runs comparisons, following 



def run_compare(infile='test.run',pffile='default',outfile='default'):
	'''

	Run the model comparisons based on what is in the .ls file
	'''

	# Read the input file

	try:
		f=open(infile,'r')
		xlines=f.readlines()
		f.close()
	except IOError :
		print "This file %s does not exist" % infile   
		return
	

	# inputs=read_file(infile)

	dir,filename,root,ext=split_filename(infile)

	# Adjust the name of the parameter file

	if pffile=='default':
		pffile=root+'.pf'
	else:
		xdir,pffile,root,ext=split_filename(pffile)
		pffile=root+'.pf'



	if outfile=='default':
		outfile=infile+'.out'



	# Before starting huge numbers of runs of a routine which will failover to interactive mode
	# check if the .pf files exists

	if os.path.exists(pffile):
		print 'The pf file d %s does exist, ready to rock and roll' % pffile
	else:
		print 'The pf file d %s does not exist. Get one before trying to proceed' % pffile
		return


	# Check if the outfile exits if it does then ask whether it should be delted before beginning
	if os.path.exists(outfile):
		print 'The output file d %s already exists' % outfile
		choice=raw_input('Delete it (y/n)')
		if choice[0]=='y':
			os.remove(outfile)
		else:
			'OK, continuing with old output file '

	# Iterate over the input file, checking to see if py_comapre has
	# already been run on this combination.  If so, skip, if not
	# run add to command string

	commands=[]
	i=0
	# while i<len(inputs):
	while i<len(xlines):
		inline=xlines[i].split()

		if inline[0]=='#': # It's a comment line, so add to the output file
			g=open(outfile,'a')
			g.write(xlines[i])
			g.close()
		else:
			file1='%s.spec_smo' % inline[0]
			file2='%s.spec_smo' % inline[2]
			if os.path.exists(file1) and os.path.exists(file2):
				commandstring='py_compare -m1 %s.spec_smo %s -m2 %s.spec_smo %s -o %s %s' % (inline[0],inline[1],inline[2],inline[3],outfile,pffile)
			os.system(commandstring)
		i=i+1



	print infile,pffile,outfile


def run_self_compare(infile='test.ls',pffile='default',outfile='default',shift=1,spec_ext='spec_smo'):
	'''
	Run the a comparison on a set of models to estimate the statistical error
	in the model.

	where:
		infile 	The list of spectra to self_compare.  The routine expects a file with 
			spectrum_rootname	spectrum number, e. g. a file created by pf2ls

		pfile 	The parameter file.  On default this is set to infile root + .pf
		outfile The output file. On default, set to infile root + err.out
		shift   The shift applied to the model in the comparison
		spec_ext	The extension to the base name defining the spectrum, usually
				spec or spec_smo

	The output file is the input fiel  to analyze
	'''

	# Read the input file

	try:
		f=open(infile,'r')
		xlines=f.readlines()
		f.close()
	except IOError :
		print "This file %s does not exist" % infile   
		return
	

	# inputs=read_file(infile)

	dir,filename,root,ext=split_filename(infile)

	# Adjust the name of the parameter file

	if pffile=='default':
		pffile=root+'.pf'
	else:
		print split_filename(pffile)
		xdir,pffile,root,ext=split_filename(pffile)
		pffile=root+'.pf'



	if outfile=='default':
		outfile=root+'.err.out'



	# Before starting huge numbers of runs of a routine which will failover to interactive mode
	# check if the .pf files exists

	if os.path.exists(pffile):
		print 'The pf file %s does exist, ready to rock and roll' % pffile
	else:
		print 'The pf file %s does not exist. Get one before trying to proceed' % pffile
		return


	# Check if the outfile exits if it does then ask whether it should be delted before beginning
	if os.path.exists(outfile):
		print 'The output file d %s already exists' % outfile
		choice=raw_input('Delete it (y/n)')
		if choice[0]=='y':
			os.remove(outfile)
		else:
			'OK, continuing with old output file '

	# Write something to the file to indicate what it is. Note that more could be done with
	# this.

	g=open(outfile,'a')
	g.write('# SELFCOMPARE\n')
	g.close()

	# Iterate over the input file, checking to see if py_comapre has
	# already been run on this combination.  If so, skip, if not
	# run add to command string

	commands=[]
	i=0
	# while i<len(inputs):
	while i<len(xlines):
		inline=xlines[i].split()

		if inline[0]=='#': # It's a comment line, so add to the output file
			g=open(outfile,'a')
			g.write(xlines[i])
			g.close()
		else:
			file1='%s.%s' % (inline[0],spec_ext)
			if os.path.exists(file1):
				commandstring='py_compare -m1 %s %s -m2 %s %s -o %s -s %d %s' % (file1,inline[1],file1,inline[1],outfile,shift,pffile)
			os.system(commandstring)
		i=i+1



	print 'Files used for this routine',infile,pffile,outfile

def analyze(infile='test.run.out'):
	'''
	Analyze the results of the evaluation of the grid
	made with py_compare
	'''

	print 'Evaluating: ',os.getcwd(), 'using', infile, 'on ', datetime.date.today()

	xlines=[]

	# Read the input file

	try:
		f=open(infile,'r')
		xlines=f.readlines()
		f.close()

	except IOError :
		print "This file %s does not exist" % infile   
		return xlines



	variable='Errors'
	xx=[]

	i=0
	while i<len(xlines):
		line=xlines[i].strip()
		line=line.split()
		if line[0]=='#':
			if line[1]=='XVAR':
				if len(xx)>0:

					xx=numpy.array(xx)
					ave=numpy.average(xx)
					med=numpy.median(xx)
					min=xx.min()
					max=xx.max()
					std=xx.std()

					# print variable,len(xx),ave,med,std,min,max

					print '%-30s %5d ave %8.3f  med %8.3f std %8.3f min %8.3f max %8.3f' % (variable,len(xx),ave,med,std,min,max)

				variable=line[2]
				xx=[]
		else:
			xx.append(eval(line[4]))

		i=i+1
	

	if len(xx)>0:
		xx=numpy.array(xx)
		ave=numpy.average(xx)
		med=numpy.median(xx)
		min=xx.min()
		max=xx.max()
		std=xx.std()
		# print variable,len(xx),ave,med,std,min,max
		
		print '%-30s %5d ave %8.3f  med %8.3f std %8.3f min %8.3f max %8.3f' % (variable,len(xx),ave,med,std,min,max)





if __name__ == "__main__":
	import sys
	if len(sys.argv)>1:
		pfs2ls(sys.argv[1],sys.argv[2])
	else:
		print 'usage: grid_eval.py pfroot listroot' 
