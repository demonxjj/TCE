﻿#--coding:utf-8--



import	sys,os
from lexparser import *
from xml.dom.minidom import  parseString as xmlParseString

# if iflist is null means all interface is requred
#
def unique_append(list,new):
	for e in list:
		if e.name == new.name:
			return
	list.append(new)

def filterStruct(final,list):
	structs=[]
	for e in final:
		if not isinstance(Struct):
			continue
		structs.append(e)

def searchTypes(e,list,result):
	unique_append(result,e)
	if isinstance(e,Struct):
		for e2 in e.list:
			if not isinstance(e2,Builtin):
				searchTypes(e2,list,result)
	if isinstance(e,Sequence):
		if not isinstance(e.type,Builtin):
			searchTypes(e.type,list,result)


def filterInterface(unit,iflist,ifcnt):
#	ifcnt - 接口起始编号
#	unit - 解析语法树
#	iflist  - 语法树上的 interface对象

	import copy
	if not iflist:
		return
	ifx = []
	types=[]
	types2=[]

	#----------------------------
	# +- subfix
	ifattrs = {} #{ifname:exposed} 接口是否暴露输出delegate和servant代码
	for name in iflist:
		if name[-1] not in '+-':
			ifattrs[name] = True  # expose service
		if name[-1] == '+':
			ifattrs[name[:-1]] = True
		if name[-1] == '-':
			ifattrs[name[:-1]] = False
	iflist = ifattrs.keys()
	#----------------------------
#	print iflist
#	print ifattrs
#
	for idx,e in enumerate(unit.list):
		if not isinstance(e,Interface):
			ifx.append(e)
			continue
		e.ifidx = ifcnt #动态插入的属性
		ifcnt+=1

		if not iflist.count(e.getName()):
			continue
		e.delegate_exposed = ifattrs[e.getName()]
#		print e.delegate_exposed
#		print e.getName()


		for m in e.list:
			for p in m.params: # check params of function
				for e2 in unit.list:
					if e2.name == p.type.name:
						unique_append(types,e2)

			#check return param
			for e2 in unit.list:
				if m.type.name == e2.name:
					unique_append(types,e2)
				#
		ifx.append(e)

	for e2 in types:
		searchTypes(e2,unit.list,types2)

	types3 = ifx + types + types2

	all =[]
	for e in unit.list:
		for e2 in types3:
			if e.name == e2.name:
				unique_append(all,e)
			#	print all

	unit.list = all


#接口索引外部文件定义

# module.if-name = index,expose_delegate=true

# index - 接口的索引编号 (int)
# expose_delegate 指定是否生成 delegate委托类代码(作为服务servant)
#                 未指定默认true，表示生成委托类代码
ifidx_list = None

# def __getInterfaceIndexWithName(name):
# 	"""
# 	未定义接口名称的序号则返回 -1
# 	:param name:
# 	:return:
# 	"""
# 	import os,os.path,string
# 	global  ifidx_list
# 	if ifidx_list == None:
# 		ifxfile = "ifx-index-list.txt"
# 		if os.path.exists(ifxfile):
# 			file = open(ifxfile)
# 			content = file.readlines()
#
# 			ifidx_list = {}
# 			for line in content:
# 				line = line.strip()
# 				if not line: continue
# 				results = line.split('=')
# 				ifname,values = map(string.strip,results)
# 				cfgs = values.split(',') #接口配置参数
# 				cfgs = map(string.strip,cfgs)
# 				# index =params[0]
# 				ifidx_list[ifname] = cfgs
# 		else:
# 			print 'warning: file<%s> not found...'%ifxfile
# 			ifidx_list ={}
# 	# print ifidx_list,name
# 	cfgs  = ifidx_list.get(name)
# 	if not cfgs:
# 		return -1
# 	return int(cfgs[0])

def isExposeDelegateOfInterfaceWithName(name):
	'''
		判别 接口委托代码是否输出
		配置文件不存在或者未指定expose参数，默认返回True，也就是输出委托代码
	'''
	global  ifs_def
	loadInterfaceDefs()
	ifx = ifs_def.get(name)
	if not ifx:
		return True
	exposed = ifx.get('delegate_expose','false')
	if exposed.lower() in ('false','0'):
		return False
	return True

	# if not ifidx_list:
	# 	getInterfaceIndexWithName('')
	# if not ifidx_list:
	# 	return True
	# cfgs = ifidx_list.get(name)
	# if not cfgs:
	# 	return True
	# if len(cfgs)>1 :
	# 	exposed = cfgs[1]
	# 	if exposed.lower() in ('false','0'): #只有配置第二项为 false或者0 则屏蔽输出委托代码
	# 		return False
	# return True






IFX_INDEX_FILE='ifx-index-list.xml'


ifs_def = {}

def loadInterfaceDefs():
	global  ifs_def
	if ifs_def:
		return

	if not os.path.exists( IFX_INDEX_FILE ):
		# print 'preconfig file: %s not found,skipped..'%IFX_INDEX_FILE
		return -1

	if not ifs_def:
		f = open( IFX_INDEX_FILE)
		content = f.read()
		f.close()
		doc = xmlParseString(content)
		root = doc.documentElement  # <interfaces>
		ifs = root.getElementsByTagName('if')
		for if_ in ifs:
			name = if_.getAttribute('name')
			index = if_.getAttribute('index')
			expose = if_.getAttribute('delegate_expose')
			functions = {}
			fxs = if_.getElementsByTagName('f')

			for fx in fxs:
				f_name = fx.getAttribute('name')
				f_index = fx.getAttribute('index')
				functions[f_name] = {'index':f_index}
			ifs_def[name] = {'index':index,'delegate_expose':expose,'functions':functions}

def getInterfaceIndexWithName(name):
	"""
	xml 版本
	未定义接口名称的序号则返回 -1
	:param name:
	:return:
	"""
	global ifs_def
	loadInterfaceDefs()
	ifx = ifs_def.get(name)
	if ifx:
		return int(ifx['index'])
	return -1



def getFunctionIndexWithName(name,if_name):
	"""
	获取函数索引编号
	:param name:  函数名称
	:param if_name:  接口名称
	:return:
	  -1  － 未定义
	"""

	global  ifs_def

	loadInterfaceDefs()

	ifx = ifs_def.get(if_name)
	if ifx:
		fx = ifx['functions'].get(name)
		if fx:
			return int(fx['index'])
	return -1

def rebuildFunctionIndex(ifx):
	module = ifx.container
	for opidx,m in enumerate(ifx.list):
		m.index = opidx  # based 0 ..
		idx = getFunctionIndexWithName( m.name,"%s.%s"%(module.name,ifx.name))
		if idx != -1:
			m.index = idx