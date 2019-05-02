from collections import defaultdict
import couchdb


def allExtGroup(component_list):
    i = 0
    base_ext_group = defaultdict(list)
    current_ext_group = ""
    while (i < len(component_list)):
        if current_ext_group == "" and component_list[i][3] == "B":
            current_ext_group = component_list[i][0] + "_" + component_list[i][1]+ "_"+component_list[i][4]+"_"+component_list[i][2]
            base_ext_group[current_ext_group] = []
        elif current_ext_group != "" and component_list[i][3] == "B":
            base_ext_group[current_ext_group].append(component_list[i][0] + "_" + component_list[i][1]+ "_"+component_list[i][4])
        if current_ext_group != "" and component_list[i][0] == current_ext_group.split("_")[0] and \
                component_list[i][3] == "E":
            current_ext_group = ""
        i += 1
    for key in base_ext_group:
        yield key.split("_")

def allIntGroup(component_list,key1 = None):
    i = 0
    base_ext_group = defaultdict(list)
    current_ext_group = ""
    while (i < len(component_list)):
        if current_ext_group == "" and component_list[i][3] == "B":
            current_ext_group = component_list[i][0] + "_" + component_list[i][1] + "_" + component_list[i][4] + "_" + \
                                component_list[i][2]
            base_ext_group[current_ext_group] = []
        elif current_ext_group != "" and component_list[i][3] == "B":
            base_ext_group[current_ext_group].append(
                component_list[i][0] + "_" + component_list[i][1] + "_" + component_list[i][4])
        if current_ext_group != "" and component_list[i][0] == current_ext_group.split("_")[0] and \
                component_list[i][3] == "E":
            current_ext_group = ""
        i += 1
    if key1 is None:
        for key in base_ext_group:
            for value in base_ext_group[key]:
                yield value.split("_")
    else:
        return base_ext_group[key1] if key1 in base_ext_group else None

def getAllinternalgroups(component_list,key):
    i = 0
    base_ext_group = defaultdict(list)
    current_ext_group = ""
    while (i < len(component_list)):
        if current_ext_group == "" and component_list[i][3] == "B":
            current_ext_group = component_list[i][0] + "_" + component_list[i][1]
            base_ext_group[current_ext_group] = []
        elif current_ext_group != "" and component_list[i][3] == "B":
            base_ext_group[current_ext_group].append(
                component_list[i][0] + "_" + component_list[i][1])
        if current_ext_group != "" and component_list[i][0] == current_ext_group.split("_")[0] and \
                component_list[i][3] == "E":
            current_ext_group = ""
        i += 1
    if key[0]+"_"+key[1] in base_ext_group:
        return base_ext_group[key[0]+"_"+key[1]]
    else:
        return None


def decodeType(data):
    if data == "ID" or data == "AN":
        type = "string"
    elif data == "DT":
        type = "date"
    elif data == "TM":
        type = "time"
    else:
        type = "numeric"
    return type

ElementDict = defaultdict(list)
couchserver = couchdb.Server("http://%s:%s@9.199.145.193:5984/" % ("admin", "admin123"))
element_db = couchserver['elementusagedefs2']

def getElementPosition(element,version,segment):
    if segment in ElementDict:
        currentelement= ElementDict[segment].index(element)
        return ElementDict[segment][currentelement-1]
    else:
        for row in element_db.view('_design/elem-search/_view/elem-search', key=[version, segment]):
            ElementDict[segment].append(row.value[0])
        currentelement = ElementDict[segment].index(element)
        return ElementDict[segment][currentelement - 1]

def getSegmentPosition(segmentitem , componentlist,t):
    for data in componentlist:
        if data[0] == segmentitem[0] and data[1] == segmentitem[1]:
            index = componentlist.index(data)
            prevType = "Segment"
            if componentlist[index - 1][0] != segmentitem[0]:
                prevType = "Group"
            return componentlist[index - 1], prevType
        elif data[0] == ""  and segmentitem[0] == t:
            index = componentlist.index(data)
            prevType = "Segment"
            if componentlist[index - 1][0] != segmentitem[0]:
                prevType = "Group"
            return componentlist[index - 1], prevType

def getGroupPosition(groupitem,componentlist,t):
    for data in componentlist:
        if data[0] == groupitem[0] and data[1] == groupitem[1] and data[3] == "B":
            index = componentlist.index(data)
            prevType = "Segment"
            if componentlist[index - 1][3] == 'E':
                prevType = "Group"
            if componentlist[index - 1][0] == "":
                componentlist[index - 1][0] = t
            return componentlist[index - 1], prevType


def getCorrectgroupName(part1,part2):
    if part1 == part2:
        return part1
    else:
        return part1+"_"+part2