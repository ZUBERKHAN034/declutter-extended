from fnmatch import fnmatch
import logging
import os
import re
from pathlib import Path
from shutil import copytree, rmtree
from time import time
from send2trash import send2trash
from zeno.store import load_settings
from zeno.file_utils import (get_file_time, convert_to_days, get_size, advanced_copy,
                         advanced_move, get_file_type,
                         _escape_glob)
from zeno.core.file_guard import is_file_ready

def apply_rule(rule, dryrun=False):
    report = {'copied': 0, 'moved': 0, 'moved to subfolder': 0, 'deleted': 0,
              'trashed': 0, 'renamed': 0}
    details = []
    if rule['enabled']:
        files = get_files_affected_by_rule(rule)
        if files:
            logging.debug(
                "Processing rule" + (" [DRYRUN mode]" if dryrun else "") + ": " + rule['name'])
            for f in files:
                msg = ""
                p = Path(f)
                if rule['action'] == 'Copy':
                    target_folder = resolve_path(rule['target_folder'], p)
                    target = Path(target_folder) / str(p).replace(':', '') if ('keep_folder_structure' in rule.keys(
                    ) and rule['keep_folder_structure']) else Path(target_folder) / p.name
                    try:
                        if p.is_dir():
                            if target.is_dir():
                                # TBD replaces only if size differs
                                if get_size(target) != get_size(f):
                                    if not dryrun:
                                        rmtree(target)
                                        result = copytree(f, target)
                                        # hide_dc(result) # TBD only for sidecar files
                                        msg = "Replaced " + str(result) + " with " + f
                                    report['copied'] += 1
                            else:
                                if not dryrun:
                                    # TBD will probably crash if target exists!
                                    result = copytree(f, target)
                                    # hide_dc(result) # TBD only for sidecar files
                                msg = "Copied " + f + " to " + str(result)
                                report['copied'] += 1
                        else:
                            if target.is_file() and os.stat(target).st_size == os.stat(f).st_size:  # TBD comparing sizes may be not enough
                                msg = "File " + f + " already exists in the target location and has the same size, skipping"
                            else:
                                if not dryrun:
                                    result = advanced_copy(
                                        f, target, (rule['overwrite_switch'] == 'overwrite') if 'overwrite_switch' in rule.keys() else False)
                                else:
                                    msg = "Copied " + f + " to " + str(result)
                                if result:
                                    report['copied'] += 1
                                    msg = "Copied " + f + " to " + str(result)
                    except Exception as e:
                        logging.exception(f'exception {e}')
                elif rule['action'] == 'Move':
                    if not dryrun:
                        target_folder = resolve_path(rule['target_folder'], p)
                        target = Path(target_folder) / str(p).replace(':', '') if ('keep_folder_structure' in rule.keys(
                        ) and rule['keep_folder_structure']) else Path(target_folder) / p.name
                        try:
                            result = advanced_move(
                                f, target, (rule['overwrite_switch'] == 'overwrite') if 'overwrite_switch' in rule.keys() else False)
                            if result:
                                msg = "Moved " + f + " to " + str(result)
                                report['moved'] += 1
                        except Exception as e:
                            logging.exception(f'exception {e}')
                    else:
                        msg = "Moved " + f + " to " + target_folder
                elif rule['action'] == 'Rename':
                    if 'name_pattern' in rule.keys() and rule['name_pattern']:
                        newname = rule['name_pattern'].replace(
                            '<filename>', p.name)
                        newname = newname.replace('<folder>', p.parent.name)
                        # TBD what if there are multiple replace tokens?
                        rep = re.findall("<replace:(.*):(.*)>", newname)
                        newname = re.sub("<replace(.*?)>", '', newname)
                        for r in rep:
                            newname = newname.replace(r[0], r[1])
                        if not dryrun:
                            try:
                                result = advanced_move(p, Path(
                                    p.parent) / newname, (rule['overwrite_switch'] == 'overwrite') if 'overwrite_switch' in rule.keys() else False)
                                if result:
                                    newfullname = Path(p.parent / newname)
                                    if newfullname.is_dir():  # if renamed a folder check if its children are in the list, and if they are update their paths
                                        for i in range(len(files)):
                                            if p in Path(files[i]).parents:
                                                files[i] = files[i].replace(
                                                    str(p), str(newfullname))
                                    # tf = get_tag_file_path(f) # TBD bring this back for sidecar files
                                    # if tf.is_file():
                                    #     os.chdir(tf.parent)
                                    #     os.rename(tf.name, newname + '.json')
                                    report['renamed'] += 1
                                    msg = 'Renamed ' + f + ' to ' + str(result)
                            except Exception as e:
                                logging.exception(e)
                        else:
                            msg = 'Renamed ' + f + ' to ' + newname
                    else:
                        msg = 'Error: name pattern is missing for rule ' + \
                            rule['name']
                        logging.error(
                            "Name pattern is missing for rule " + rule['name'])
                elif rule['action'] == 'Move to subfolder':
                    target_subfolder = resolve_path(
                        rule['target_subfolder'], p)
                    if p.parent.name != target_subfolder:  # check if we're not already in the subfolder
                        if not dryrun:
                            result = advanced_move(f, p.parent / Path(target_subfolder) / p.name, (
                                rule['overwrite_switch'] == 'overwrite') if 'overwrite_switch' in rule.keys() else False)
                            if result:
                                report['moved to subfolder'] += 1
                                msg = "Moved " + f + " to subfolder: " + \
                                    str(target_subfolder)
                        else:
                            msg = "Moved " + f + " to subfolder: " + \
                                str(target_subfolder)
                elif rule['action'] == 'Delete':
                    msg = "Deleted " + f
                    if not dryrun:
                        report['deleted'] += 1
                        os.remove(f)
                elif rule['action'] == 'Send to Trash':
                    msg = "Sent to trash " + f
                    if not dryrun:
                        report['trashed'] += 1
                        send2trash(f)
                if msg:
                    details.append(msg)
                    logging.debug(msg)
    # else:
    #     logging.debug("Rule "+rule['name'] + " disabled, skipping.")
    return report, details

# resolves patterns in target_folder name
# <type> replaced with the type of path (uses types from settings), if the type can't be resolved, replaced with None

def resolve_path(target_folder, path):
    final_path = target_folder.replace('<type>', get_file_type(path))
    return final_path


def apply_all_rules(settings):
    report = {}
    details = []
    for rule in settings['rules']:
        # TBD doesn't look optimal / had to use load_settings for testing, should be just settings
        rule_report, rule_details = apply_rule(rule, load_settings()['dryrun'])
        report = {k: report.get(k, 0) + rule_report.get(k, 0)
                  for k in set(report) | set(rule_report)}
        details.extend(rule_details)
    return report, details

def get_files_affected_by_rule(rule, allow_empty_conditions=False):
    if (not 'conditions' in rule.keys() or not rule['conditions']) and not allow_empty_conditions:
        return ([])
    found = []
    for f in rule['folders']:
        if Path(f).is_dir():
            found.extend(get_files_affected_by_rule_folder(rule, f, []))
        else:
            logging.error('Folder ' + f + ' in rule ' +
                          rule['name'] + ' doesn\'t exist, skipping')
    if 'ignore_newest' in rule.keys() and rule['ignore_newest']:
        folders = {}
        result = []
        for f in found:
            if os.path.isfile(f):
                folder = Path(f).parent
                if not folder in folders.keys():
                    folders[folder] = []
                folders[folder].append(f)
            else:
                result.append(f)

        for val in folders.values():
            unsorted_files = {}
            for sf in val:
                unsorted_files[sf] = get_file_time(sf)
            sorted_files = {k: v for k, v in sorted(
                unsorted_files.items(), key=lambda item: -item[1])}
            target_list = list(sorted_files)[int(rule['ignore_N']):]
            result.extend(target_list)

        return result
    else:
        return sorted(list(set(found)))  # returning only unique results



def get_files_affected_by_rule_folder(rule, dirname, files_found=None):
    files = os.listdir(dirname)
    out_files = files_found if files_found is not None else []
    for f in files:
        if f != '.dc':  # ignoring .dc folder TBD can be removed for now and brough back for sidecar files
            fullname = os.path.join(dirname, f)
            if rule['action'] == 'Move to subfolder' and ((Path(fullname).parent).name == rule['target_subfolder'] or (Path(fullname).is_dir() and f == rule['target_subfolder'])):
                conditions_met = False
            else:
                conditions_met = False if rule['condition_switch'] == 'any' else True
                for c in rule['conditions']:
                    condition_met = False
                    if c['type'] == 'date':
                        try:
                            settings = load_settings()
                            if c['age_switch'] == '>=':
                                if (float(time()) - get_file_time(fullname, settings['date_type']))/(3600*24) >= convert_to_days(float(c['age']), c['age_units']):
                                    condition_met = True
                            elif c['age_switch'] == '<':
                                if (float(time()) - get_file_time(fullname, settings['date_type']))/(3600*24) < convert_to_days(float(c['age']), c['age_units']):
                                    condition_met = True
                        except Exception as e:
                            logging.exception(e)
                    elif c['type'] == 'size' and os.path.isfile(fullname):
                        factor = {'B': 1, 'KB': 1024 ** 1, 'MB': 1024 **
                                  2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}
                        fsize = os.stat(fullname).st_size
                        target_size = float(c['size']) * \
                            factor[c['size_units']]
                        if c['size_switch'] == '>=':
                            condition_met = fsize >= target_size
                        elif c['size_switch'] == '<':
                            condition_met = fsize < target_size
                    elif c['type'] == 'name':
                        if not 'name_switch' in c.keys():  # TBD this is temporary to support old conditions that don't have this switch yet
                            c['name_switch'] = 'matches'
                        # TBD need to reflect this in help - it works like this: 'matches any' or 'doesn't match all'
                        for m in c['filemask'].split(','):
                            condition_met = condition_met or fnmatch(
                                _escape_glob(f), m.strip())
                            if condition_met:
                                break
                        condition_met = condition_met == (
                            c['name_switch'] == 'matches')
                    elif c['type'] == 'type' and os.path.isfile(fullname):
                        condition_met = (get_file_type(fullname) == c['file_type']) == (
                            c['file_type_switch'] == 'is')

                    if rule['condition_switch'] == 'any':
                        conditions_met = conditions_met or condition_met
                        if conditions_met:
                            break
                    elif rule['condition_switch'] == 'all':
                        conditions_met = conditions_met and condition_met
                        if not conditions_met:
                            break
                    elif rule['condition_switch'] == 'none':
                        conditions_met = conditions_met and not condition_met
                        if not conditions_met:
                            break

            if conditions_met:
                if not is_file_ready(fullname):
                    logging.debug(f"[Guard] SKIP — file not ready: {fullname}")
                else:
                    out_files.append(os.path.normpath(fullname))

            # Recurse for 'Rename'; for other actions skip already-matched folders
            if (rule['action'] == 'Rename' or not conditions_met) and os.path.isdir(fullname) and rule['recursive']:
                # if not conditions_met and os.path.isdir(fullname) and rule['recursive']:
                get_files_affected_by_rule_folder(rule, fullname, out_files)
    return out_files

def get_rule_by_name(name):
    settings = load_settings()
    for r in settings['rules']:
        if r['name'] == name:
            return r

def get_rule_by_id(rule_id, rules=[]):
    if not rules:
        rules = load_settings()['rules']
    for r in rules:
        if int(r['id']) == rule_id:
            return r
