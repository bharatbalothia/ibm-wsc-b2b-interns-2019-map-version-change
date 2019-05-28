import couchdb
from bs4 import BeautifulSoup
from collections import defaultdict
from ediUtils import ediUtils
from operator import itemgetter
import json
import itertools



def change(targettemplate,basefile,targetversion,finalMap,new_map_name):
    target_template = targettemplate
    print(targettemplate)
    basemap = basefile
    couchserver = couchdb.Server("http://%s:%s@9.199.145.193:5984/" % ("admin", "admin123"))
    element_db = couchserver['elementusagedefs2']
    segment_db = couchserver["segmentusagedefs"]
    target_version = targetversion
    f1 = open(basemap,encoding="utf-8")
    f2 = open(target_template,encoding="utf-8")
    soup1 = BeautifulSoup(f2.read(), 'lxml-xml')
    soup2 = BeautifulSoup(f1.read(), 'lxml-xml')
    Utils = ediUtils()

    soup2.MapDetails.Summary.Description.contents[0].replaceWith(new_map_name)

    print(soup2.MapDetails.Summary.Description.text)

    if soup2.MapDetails.EDIAssociations_OUT.VersionID.text != "":
        map_type = "OUTBOUND"
        transaction = soup2.MapDetails.EDIAssociations_OUT.BindingID.text
        base_version = soup2.MapDetails.EDIAssociations_OUT.VersionID.text
        soup2.MapDetails.EDIAssociations_OUT.VersionID.contents[0].replaceWith(target_version)
    else:
        map_type = "INBOUND"
        transaction = soup2.MapDetails.EDIAssociations_IN.BindingID.text
        base_version = soup2.MapDetails.EDIAssociations_IN.VersionID.text
        soup2.MapDetails.EDIAssociations_IN.VersionID.contents[0].replaceWith(target_version)

    name_map = defaultdict(list)
    base_component_list = [row.value for row in segment_db.view('_design/full_list/_view/full_list', key=[base_version, transaction])]
    target_componet_list = [row.value for row in segment_db.view('_design/full_list/_view/full_list', key=[target_version, transaction])]
    
    main_groups_org = {data[1]:[data[0],data[2]] for data in Utils.allExtGroup(base_component_list)}
    main_groups_final = {data[1]:[data[0],data[2]] for data in Utils.allExtGroup(target_componet_list)}
    
    main_seg_org = {data.value[0]: data.value[1] for data in segment_db.view('_design/looping-view/_view/looping-view', key=[base_version, transaction])}
    main_seg_final = {data.value[0]: data.value[1] for data in segment_db.view('_design/looping-view/_view/looping-view', key=[target_version, transaction])}
    
    sess = defaultdict(list)
    sess['seg_to_be_deleted'] = [[transaction,x] for x in main_seg_org if x not in main_seg_final]
    sess['seg_to_be_added'] = [[transaction,x] for x in main_seg_final if x not in main_seg_org]
    common_main_segments = [x for x in main_seg_org if x in main_seg_final]
    sess['seg_looping_change'] = [[transaction, i, main_seg_org[i], main_seg_final[i]] for i in common_main_segments if main_seg_org[i] != main_seg_final[i]]
    
    
    sess['grp_to_be_deleted'] = [[main_groups_org[x][0],x] for x in main_groups_org if x not in main_groups_final]
    sess['grp_to_be_added'] = [[main_groups_final[x][0],x] for x in main_groups_final if x not in main_groups_org]
    common_main_groups = []
    main_grp_name = []
    for x in main_groups_org:
        if x in main_groups_final:
            common_main_groups.append(x)
            name_map[(x, main_groups_org[x][0])].append([x,main_groups_final[x][0]])
            main_grp_name.append([main_groups_org[x][0],main_groups_final[x][0],x])
    sess['group_looping_change'] = [[main_groups_org[i][0], i, main_groups_org[i][1], main_groups_final[i][1]] for i in common_main_groups if main_groups_org[i][1] != main_groups_final[i][1]]
    
    
    for seg in common_main_segments:
        segment_element_org ={}
        segment_element_final = {}
        common_elements = []
        for row in element_db.view('_design/elem-search/_view/elem-search', key=[base_version, seg]):
            doc = {
                'length': [row.value[1], row.value[2]],
                'type': Utils.decodeType(row.value[3])
            }
            segment_element_org[row.value[0]] = doc
        for row in element_db.view('_design/elem-search/_view/elem-search', key=[target_version, seg]):
            doc = {
                'length': [row.value[1], row.value[2]],
                'type': Utils.decodeType(row.value[3])
            }
            segment_element_final[row.value[0]] = doc
        for elem in segment_element_final:
            if elem not in segment_element_org:
                sess['elem_to_be_added'].append([transaction, seg, elem])
    
        for elem in segment_element_org:
            if elem not in segment_element_final:
                sess['elem_to_be_deleted'].append([transaction, seg, elem])
            else:
                common_elements.append(elem)
        for elem in common_elements:
            if segment_element_org[elem]['length'] != segment_element_final[elem]['length']:
                sess['elem_length_change'].append([transaction, seg, elem, segment_element_org[elem]['length'][0], segment_element_org[elem]['length'][1],
                     segment_element_final[elem]['length'][0], segment_element_final[elem]['length'][1]])
            if segment_element_org[elem]['type'] != segment_element_final[elem]['type']:
                sess['elem_type_change'].append(
                    [transaction, seg, elem, segment_element_org[elem]['type'], segment_element_final[elem]['type']])
    
    
    internal_groups_org = defaultdict(list)
    internal_group_length_org = {}
    internal_group_list_org =[]
    for data in Utils.allIntGroup(base_component_list):
        internal_group_list_org.append(data[1])
        internal_group_length_org[data[0]] = data[2]
        internal_groups_org[data[1]].append(data[0])
    internal_groups_final = defaultdict(list)
    internal_group_length_final = {}
    internal_group_list_final = []
    for data in Utils.allIntGroup(target_componet_list):
        internal_group_list_final.append(data[1])
        internal_group_length_final[data[0]] = data[2]
        internal_groups_final[data[1]].append(data[0])
    
    
    for grp in common_main_groups:
        grp_seg_org ={data.value[0]: data.value[1] for data in segment_db.view('_design/group-group-seg/_view/group-group-seg',key=[base_version, transaction, main_groups_org[grp][0]])}
        grp_seg_final ={data.value[0]: data.value[1] for data in segment_db.view('_design/group-group-seg/_view/group-group-seg',key=[target_version, transaction, main_groups_final[grp][0]])}
        common_grp_seg = []
        for j in grp_seg_org:
            if j not in grp_seg_final:
                sess['seg_to_be_deleted'].append([main_groups_org[grp][0], j])
            else:
                common_grp_seg.append(j)
        sess['seg_to_be_added'] = sess['seg_to_be_added'] + [[main_groups_final[grp][0], seg] for seg in grp_seg_final if seg not in grp_seg_org]
        sess['seg_looping_change'] = sess['seg_looping_change'] + [[main_groups_org[grp][0],seg,grp_seg_org[seg],grp_seg_final[seg]] for seg in common_grp_seg if grp_seg_org[seg] != grp_seg_final[seg]]
    
        for seg in common_grp_seg:
            segment_element_org = {}
            segment_element_final = {}
            common_elements = []
            for row in element_db.view('_design/elem-search/_view/elem-search', key=[base_version, seg]):
                doc = {
                    'length': [row.value[1], row.value[2]],
                    'type': Utils.decodeType(row.value[3])
                }
                segment_element_org[row.value[0]] = doc
            for row in element_db.view('_design/elem-search/_view/elem-search', key=[target_version, seg]):
                doc = {
                    'length': [row.value[1], row.value[2]],
                    'type': Utils.decodeType(row.value[3])
                }
                segment_element_final[row.value[0]] = doc
            for elem in segment_element_final:
                if elem not in segment_element_org:
                    sess['elem_to_be_added'].append([main_groups_final[grp][0], seg, elem])
    
            for elem in segment_element_org:
                if elem not in segment_element_final:
                    sess['elem_to_be_deleted'].append([main_groups_org[grp][0], seg, elem])
                else:
                    common_elements.append(elem)
            for elem in common_elements:
                if segment_element_org[elem]['length'] != segment_element_final[elem]['length']:
                    sess['elem_length_change'].append([main_groups_org[grp][0], seg, elem, segment_element_org[elem]['length'][0],
                                                          segment_element_org[elem]['length'][1],
                                                          segment_element_final[elem]['length'][0],
                                                          segment_element_final[elem]['length'][1]])
                if segment_element_org[elem]['type'] != segment_element_final[elem]['type']:
                    sess['elem_type_change'].append(
                        [main_groups_org[grp][0], seg, elem, segment_element_org[elem]['type'], segment_element_final[elem]['type']])

    for grp in sess['grp_to_be_deleted']:
        grp_result = Utils.getAllinternalgroups(base_component_list, grp)
        if grp_result is not None:
            for k in list(internal_groups_org):
                for x in internal_groups_org[k]:
                    if x in [p.split("_")[0] for p in grp_result]:
                        internal_groups_org[k].remove(x)
                    if len(internal_groups_org[k]) == 0:
                        del internal_groups_org[k]

    for grp in sess['grp_to_be_added']:
        grp_result = Utils.getAllinternalgroups(target_componet_list, grp)
        if grp_result is not None:
            for k in list(internal_groups_final):
                for x in internal_groups_final[k]:
                    if x in [p.split("_")[0] for p in grp_result]:
                        internal_groups_final[k].remove(x)
                    if len(internal_groups_final[k]) == 0:
                        del internal_groups_final[k]

    print(internal_groups_org)
    print(internal_groups_final)
    print(internal_group_list_final)
    print(internal_group_list_org)

    grp_common = []
    for i in internal_group_list_final:
        if internal_group_list_org.count(i) == internal_group_list_final.count(i):
            grp_common.append(i)

    for i in internal_groups_org:
        if i in internal_groups_final:
            for x, y in itertools.zip_longest(internal_groups_org[i], internal_groups_final[i]):
                if x is not None and y is not None:
                    name_map[(i, x)].append([i,y])
                elif y is None:
                    sess['grp_to_be_deleted'].append([x, i])
                elif x is None:
                    sess['grp_to_be_added'].append([y, i])
        if i not in internal_groups_final:
            for x in internal_groups_org[i]:
                sess['grp_to_be_deleted'].append([x, i])
    for i in internal_groups_final:
        if i not in internal_groups_org:
            for x in internal_groups_final[i]:
                sess['grp_to_be_added'].append([x, i])

    print(name_map)

    for grp in list(set(grp_common)):
        for position in range(0,len(internal_groups_org[grp])):
            grp_seg_org = {data.value[0]: data.value[1] for data in
                           segment_db.view('_design/group-group-seg/_view/group-group-seg',
                                           key=[base_version, transaction, internal_groups_org[grp][position]])}
            grp_seg_final = {data.value[0]: data.value[1] for data in
                             segment_db.view('_design/group-group-seg/_view/group-group-seg',
                                             key=[target_version, transaction, internal_groups_final[grp][position]])}
            common_grp_seg = []
            #print(j)
            for j in grp_seg_org:
                if j not in grp_seg_final:
                    sess['seg_to_be_deleted'].append([internal_groups_org[grp][position], j])
                else:
                    common_grp_seg.append(j)
            sess['seg_to_be_added'] = sess['seg_to_be_added'] + [[internal_groups_final[grp][position], seg] for seg in
                                                                       grp_seg_final
                                                                       if seg not in grp_seg_org]
            sess['seg_looping_change'] = sess['seg_looping_change'] + [
                [internal_groups_org[grp][position], seg, grp_seg_org[seg], grp_seg_final[seg]] for seg in common_grp_seg if
                grp_seg_org[seg] != grp_seg_final[seg]]
    
            for seg in common_grp_seg:
                segment_element_org = {}
                segment_element_final = {}
                common_elements = []
                for row in element_db.view('_design/elem-search/_view/elem-search', key=[base_version, seg]):
                    doc = {
                        'length': [row.value[1], row.value[2]],
                        'type': Utils.decodeType(row.value[3])
                    }
                    segment_element_org[row.value[0]] = doc
                for row in element_db.view('_design/elem-search/_view/elem-search', key=[target_version, seg]):
                    doc = {
                        'length': [row.value[1], row.value[2]],
                        'type': Utils.decodeType(row.value[3])
                    }
                    segment_element_final[row.value[0]] = doc
                for elem in segment_element_final:
                    if elem not in segment_element_org:
                        sess['elem_to_be_added'].append([internal_groups_final[grp][position], seg, elem])
    
                for elem in segment_element_org:
                    if elem not in segment_element_final:
                        sess['elem_to_be_deleted'].append([internal_groups_org[grp][position], seg, elem])
                    else:
                        common_elements.append(elem)
                for elem in common_elements:
                    if segment_element_org[elem]['length'] != segment_element_final[elem]['length']:
                        sess['elem_length_change'].append(
                            [internal_groups_org[grp][position], seg, elem, segment_element_org[elem]['length'][0],
                             segment_element_org[elem]['length'][1],
                             segment_element_final[elem]['length'][0],
                             segment_element_final[elem]['length'][1]])
                    if segment_element_org[elem]['type'] != segment_element_final[elem]['type']:
                        sess['elem_type_change'].append(
                            [internal_groups_org[grp][position], seg, elem, segment_element_org[elem]['type'],
                             segment_element_final[elem]['type']])

    
    #deleting items
    for group in soup2.find_all('Group'):
        if group.Name is not None and group.Name.text != transaction and len(group.Name.text.split("_"))>1 and [group.Name.text.split("_")[0],group.Name.text.split("_")[1]] in sess['grp_to_be_deleted']:
            group.decompose()
            continue
        for segment in group.find_all('Segment'):
            if [group.Name.text.split("_")[0],segment.Name.text.split(":")[0]] in sess['seg_to_be_deleted']:
                segment.decompose()
                continue
            for element in segment.find_all('Field'):
                if [group.Name.text.split("_")[0],segment.Name.text.split(":")[0],element.Name.text.split(":")[0]] in sess['elem_to_be_deleted']:
                    element.decompose()
    
    
    group_loop_change = [[p,q] for p,q,r,s in sess['group_looping_change']]
    segment_loop_change = [[p,q] for p,q,r,s in sess['seg_looping_change']]
    element_loop_change = [[p,q,r] for p,q,r,s,t,u,v in sess['elem_length_change']]
    
    #changing lengths
    for group in soup2.find_all('Group'):
        if group.Name is not None and group.Name.text != transaction and len(group.Name.text.split("_"))>1 and [group.Name.text.split("_")[0],group.Name.text.split("_")[1]] in group_loop_change:
            group.Max.contents[0].replaceWith(sess['group_looping_change'][group_loop_change.index([group.Name.text.split("_")[0],group.Name.text.split("_")[1]])][3])
        for segment in group.find_all('Segment'):
            if [group.Name.text.split("_")[0],segment.Name.text.split(":")[0]] in segment_loop_change:
                segment.Max.contents[0].replaceWith(sess['seg_looping_change'][segment_loop_change.index([group.Name.text.split("_")[0],segment.Name.text.split(":")[0]])][3])
            for element in segment.find_all('Field'):
                if [group.Name.text.split("_")[0], segment.Name.text.split(":")[0], element.Name.text.split(":")[0]] in element_loop_change:
                    element.StoreLimit.MaxLen.contents[0].replaceWith(sess['elem_length_change'][element_loop_change.index([group.Name.text.split("_")[0], segment.Name.text.split(":")[0], element.Name.text.split(":")[0]])][5])
                    element.StoreLimit.MinLen.contents[0].replaceWith(sess['elem_length_change'][element_loop_change.index(
                        [group.Name.text.split("_")[0], segment.Name.text.split(":")[0], element.Name.text.split(":")[0]])][6])
    
    
    #adding element items
    foundElement = {}
    for group,seg,elem in sess['elem_to_be_added']:
        previousElement = Utils.getElementPosition(elem,target_version,seg)
        actualElement = ""
        for segments in soup1.find_all('Segment'):
            if segments.Name and segments.Name.text.split(":")[0] == seg:
                for field in segments.find_all("Field"):
                    if field.Name and field.Name.text.split(":")[0] == elem:
                        actualElement = field
                        break
                break
        for segments in soup2.find_all('Segment'):
            if segments.Name and segments.Name.text.split(":")[0] == seg:
                for field in segments.find_all("Field"):
                    if field.Name and field.Name.text.split(":")[0] == previousElement:
                        field.insert_after(actualElement)
                        break
                break
                #print(segments.Name.text)
    
    
    # Group Name Change
    '''
    group_list_org = []
    group_list_final = []
    new_group_names = [i[0] + "_" + i[1] for i in sess['grp_to_be_added']]  # names of new groups which will be added later
    deleted_group_names = [i[0] + "_" + i[1] for i in sess['grp_to_be_deleted']]
    for i in target_componet_list:
        if i[3] == 'B' and i[0] + "_" + i[1] not in new_group_names:  # check and remove new group from final list
            group_list_final.append([i[0] + "_" + i[1], i[1]])
    for i in base_component_list:
        if i[3] == 'B' and i[0] + "_" + i[1] not in deleted_group_names:
            group_list_org.append([i[0] + "_" + i[1], i[1]])
    
    
    i = 0
    j = 0
    print(group_list_org)
    print(group_list_final)
    while i < len(group_list_org) and j < len(group_list_final):
        if group_list_org[i][1] == group_list_final[j][1]:
            for grp in soup2.find_all('Group'):
                if grp.Name.text == group_list_org[i][0]:
                    grp.Name.contents[0].replaceWith(group_list_final[j][0])
                    i += 1
                    j += 1
                    break
        else:
            i += 1
            j += 1
    
    for grp in soup2.find_all('Group'):
        if len(grp.Name.text.split("_")) > 1 and (grp.Name.text.split("_")[1], grp.Name.text.split("_")[0]) in name_map:
            print("name changed")
            grp.Name.contents[0].replaceWith(
                Utils.getCorrectgroupName(name_map[(grp.Name.text.split("_")[1], grp.Name.text.split("_")[0])][1],
                                             name_map[(grp.Name.text.split("_")[1], grp.Name.text.split("_")[0])][0]))
    '''
    onemoreitr = {}
    for grp in soup2.find_all('Group'):
        groupname = grp.Name.text.split(":")[0].split("_")
        print(groupname)
        if len(groupname) > 1 and (groupname[1], groupname[0]) in name_map:
            grp.Name.contents[0].replaceWith(Utils.getCorrectgroupName(name_map[(groupname[1], groupname[0])][0][1],
                                                                          name_map[(groupname[1], groupname[0])][0][0]))
            #onemoreitr[(groupname[1], groupname[0])] =  name_map[(groupname[1], groupname[0])].pop(0)
            #if not name_map[(groupname[1], groupname[0])]:
                #del name_map[(groupname[1], groupname[0])]
        elif len(groupname) <= 1 and (groupname[0], groupname[0]) in name_map:
            print(grp.Name.text, groupname)
            grp.Name.contents[0].replaceWith(Utils.getCorrectgroupName(name_map[(groupname[0], groupname[0])][0][1],
                                                                          name_map[(groupname[0], groupname[0])][0][0]))
            name_map[(groupname[0], groupname[0])].pop(0)
            if not name_map[(groupname[0], groupname[0])]:
                del name_map[(groupname[0], groupname[0])]
        print(name_map)

    # segment Added
    for group,seg in sess['seg_to_be_added']:
        previousitem = Utils.getSegmentPosition([group,seg],target_componet_list,transaction)
        print(previousitem)
        to_be_added = ""
        for grp in soup1.find_all("Group"):
            if grp.Name and grp.Name.text.split("_")[0] == group:
                for segments in grp.find_all("Segment"):
                    if segments.Name and segments.Name.text.split(":")[0] == seg:
                        to_be_added = segments
                        break
                        # print(to_be_added)
        if previousitem[1] == "Segment":
            for grp in soup2.find_all("Group"):
                if grp.Name and grp.Name.text.split("_")[0] == previousitem[0][0]:
                    for seg in grp.find_all("Segment"):
                        if seg.Name and seg.Name.text.split(":")[0] == previousitem[0][1]:
                            seg.insert_after(to_be_added)
                            break
                    break
        elif previousitem[1] == "Group":
            for grp in soup2.find_all("Group"):
                if grp.Name and grp.Name.text.split("_")[0] == previousitem[0][0]:
                    grp.insert_after(to_be_added)
    
    #group added
    for group,seg in sess['grp_to_be_added']:
        previousitem = Utils.getGroupPosition([group,seg],target_componet_list,transaction)
        print(previousitem)
        to_be_added = ""
        for grp in soup1.find_all("Group"):
            if grp.Name and grp.Name.text == group+"_"+seg :
                to_be_added = grp
                break
        # print(to_be_added)
        if previousitem[1] == "Segment":
            for grp in soup2.find_all("Group"):
                if grp.Name and grp.Name.text.split("_")[0] == previousitem[0][0]:
                    for seg in grp.find_all("Segment"):
                        if seg.Name and seg.Name.text.split(":")[0] == previousitem[0][1]:
                            seg.insert_after(to_be_added)
                            break
                    break
        elif previousitem[1] == "Group":
            for grp in soup2.find_all("Group"):
                if grp.Name and grp.Name.text.split("_")[0] == previousitem[0][0]:
                    grp.insert_after(to_be_added)
                    print("Inserted")

    for tag in soup2.find_all("Author"):
        print(tag.text)
        tag.contents[0].replaceWith("IBM")

    version_disc = ""
    if map_type == "OUTBOUND":
        for out in soup1.find_all("EDIAssociations_OUT"):
            version_disc = out.VersionDescription.text
        for out in soup2.find_all("EDIAssociations_OUT"):
            out.VersionDescription.contents[0].replaceWith(version_disc)
    else:
        for out in soup1.find_all("EDIAssociations_IN"):
            version_disc = out.VersionDescription.text
        for out in soup2.find_all("EDIAssociations_IN"):
            out.VersionDescription.contents[0].replaceWith(version_disc)

    f1 = open(finalMap, "w",encoding='UTF-8')
    output = str(soup2)
    f1.write(output)
    f1.close()
    print(sess['grp_to_be_added'])
    print(sess['grp_to_be_deleted'])
    print(sess['group_looping_change'])
    
    print(sorted(sess['seg_to_be_added'],key=itemgetter(0)))
    print(sorted(sess['seg_to_be_deleted'],key=itemgetter(0)))
    print(sorted(sess['seg_looping_change'],key=itemgetter(0)))
    
    print(sess['elem_to_be_added'])
    
    
    print(sess['elem_to_be_deleted'])
    print(sess['elem_length_change'])
    print(sess['elem_type_change'])
    print(sess)
    print([key for key in sess])
    return sess
