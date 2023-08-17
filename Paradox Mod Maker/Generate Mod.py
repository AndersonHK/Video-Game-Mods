import os

gpath = r" * your game folder here * "
mpath = r" * your mod folder here * "

global files
files = []

def folder(path):
        if not os.path.exists(mpath+path):
                os.mkdir(mpath+path)

def exists(path):						#if it exists in the mod folder, use the mod folder version
	if os.path.isfile(mpath+path):
		return mpath
	else:
		return gpath

class file:
        def __init__(self, path):
                self.path = path
                self.mod_file()
                global files
                files.append(self)
        
        def mod_file(self):				        #read file data
                #tpath = exists(self.path)
                tpath = gpath
                file = open(tpath+self.path,'r')
                self.data = file.read()
                file.close()

        def value_size(self, value_index, line_end):
                n_tab = self.data[value_index:line_end+1].find('\t')
                if n_tab == -1 : n_tab = 999
                n_space = self.data[value_index:line_end+1].find(' ')
                if n_space == -1 : n_space = 999
                n_endl = self.data[value_index:line_end+1].find('\n')
                if n_endl == -1 : n_endl = 999
                return min(value_index+n_space,value_index+n_tab,value_index+n_endl)

        def find_scope(self, scope):
                return self.data.find(scope)
        
        def expand_scope(self):
                pass #implement later
        
        def scope_replace(self, trigger, value, scope):
                scope_index = self.find_scope(scope)
                line_start = self.data[scope_index:].find(trigger)+scope_index
                line_end = line_start+self.data[line_start:].find('\n')
                value_index = line_start+1+self.data[line_start:line_end].find('=')
                if value_index - line_start + 1 == -1: # if the trigger is found after the equal sign, abort
                        return
                for i, c in enumerate(self.data[value_index:line_end]):
                        if c != ' ':
                                value_index = i+value_index
                                break
                value_end = self.value_size(value_index, line_end)
                self.data = self.data[:value_index]+value+self.data[value_end:]
                
        def scope_mult(self, trigger, value, scope):
                scope_index = self.find_scope(scope)
                line_start = self.data[scope_index:].find(trigger)+scope_index
                line_end = line_start+self.data[line_start:].find('\n')
                value_index = line_start+1+self.data[line_start:line_end].find('=')
                if value_index - line_start + 1 == -1: # if the trigger is found after the equal sign, abort
                        return
                for i, c in enumerate(self.data[value_index:line_end]):
                        if c.isdigit():
                                value_index = i+value_index
                                break
                value_end = self.value_size(value_index, line_end)
                self.data = self.data[:value_index]+str(float(self.data[value_index:value_end])*float(value))+self.data[value_end:]
        
        def replace_value(self, trigger, value):
                if type(value) != str:
                        value = str(value)
                last = 0
                while self.data[last:].find(trigger) != -1:
                        line_start = self.data[last:].find(trigger)+last
                        last = line_start+2
                        line_end = line_start+self.data[line_start:].find('\n')
                        value_index = line_start+1+self.data[line_start:line_end].find('=')
                        if value_index - line_start + 1 == -1: # if the trigger is found after the equal sign, abort
                                continue
                        for i, c in enumerate(self.data[value_index:line_end]):
                                if c.isdigit():
                                        value_index = i+value_index
                                        break
                        value_end = self.value_size(value_index, line_end)
                        self.data = self.data[:value_index]+value+self.data[value_end:]
        
        def mult_value(self, trigger, value):
                last = 0
                while self.data[last:].find(trigger) != -1:
                        line_start = self.data[last:].find(trigger)+last
                        last = line_start+2
                        line_end = line_start+self.data[line_start:].find('\n')
                        value_index = line_start+1+self.data[line_start:line_end].find('=')
                        if value_index - line_start - 1 == -1: # if the trigger is found after the equal sign, abort
                                continue
                        for i, c in enumerate(self.data[value_index:line_end]):
                                if c.isdigit():
                                        value_index = i+value_index
                                        break
                        value_end = self.value_size(value_index, line_end)
                        self.data = self.data[:value_index]+str(float(self.data[value_index:value_end])*float(value))+self.data[value_end:]

        def add_line(self, trigger, line, value):
                if type(value) != str:
                        value = str(value)
                last = 0
                while self.data[last:].find(trigger) != -1:
                        line_start = self.data[last:].find(trigger)+last
                        last = line_start+2
                        line_end = line_start+self.data[line_start:].find('\n')
                        for i, c in enumerate(self.data[line_start:line_end]):
                                if c.isalpha():
                                        trigger_indentation = self.data[line_start-2:line_start+i]
                                        break
                        self.data = self.data[:line_end]+trigger_indentation+line+' = '+value+self.data[line_end:]
                
        
        def save(self):                                         #save file after modding
            file = open(mpath+self.path,'w+')
            file.write(self.data)
            file.close()

##############
#mod settings#
##############


#######
#files#
#######


#save files
for file in files:
        file.save()
