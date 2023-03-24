import yaml
import sys
import re

travis_ci = {
    "script":[]
}
foundOS = False
foundLang = False

def getLang(step):
    global foundLang
    global travis_ci
    if step['uses'].startswith("actions/setup-java"):
        travis_ci["language"] = "java"
        if "with" in step and "java-version" in step["with"]:
            jdks = step["with"]["java-version"]
            if isinstance(jdks, str) or isinstance(jdks, (int, float)):
                version=str(jdks);
                if not re.fullmatch(r'-?\d+\.\d+', version) and not re.fullmatch(r'\d+', version):
                    return
                travis_ci["jdk"]=[]
                parsedJdks="openjdk"+str(jdks)
                travis_ci["jdk"].append(parsedJdks)
            elif isinstance(jdks, list) or isinstance(jdks, tuple):
                parsedJdks=[]
                for version in jdks:
                    parsedJdks.append("openjdk"+version)
                travis_ci["jdk"]+=(parsedJdks)
        foundLang = True
    elif step['uses'].startswith("actions/setup-python"):
        travis_ci["language"] = "python"
        if "with" in step and "python-version" in step["with"]:
            pyt = step["with"]["python-version"]
            travis_ci["python"]=[]
            travis_ci["python"].append(pyt)
        foundLang = True

def getOS(job):
    global foundOS
    global travis_ci
    if job["runs-on"].startswith("ubuntu"):
            travis_ci["os"] = "linux"
            foundOS = True

def getBranches(github_actions):
    global travis_ci
    branches ={}
    onlyB=[]
    foundOnly=False
    foundExcept = False # This will be used in next version of the file.
    exceptB=[] # This will be used in next version of the file.
    try:
        for key in github_actions[True].keys():
            if github_actions[True][key]["branches"] is not None:
                if github_actions[True][key]["branches"] not in onlyB:
                    onlyB+=github_actions[True][key]["branches"]
                foundOnly = True    
        if foundOnly:
            branches["only"] = list(set(onlyB))
            travis_ci["branches"] = branches
    except:
        return 

def getEventsFromObject(github_actions):
    count = len(github_actions[True].keys())
    Maincondition=""
    i=0;
    global travis_ci
    for key in github_actions[True].keys():
        condition = ("type = "+str(key))
        branches = ""
        bcount = len(github_actions[True][key]["branches"])
        j=0
        for branch in github_actions[True][key]["branches"]:
            branches+=("branch = "+branch)
            j=j+1
            if j!=bcount:
                branches+=" OR "
        if branches!="":
            if bcount != 1:
                branches = "("+branches+")"
            condition = condition + " AND " + branches
        i=i+1
        if count != 1:
            condition = "("+condition+")"
        if i != count:
            condition = condition + " OR "
        Maincondition+=condition
    travis_ci["if"]=Maincondition   

def getEventsFromArray(github_actions):
    condition=""
    global travis_ci
    count = len(github_actions[True])
    i=0
    for event in github_actions[True]:
        condition += ("type = "+ event)
        i=i+1
        if i != count:
            condition+=" OR "
    travis_ci["if"]=condition

def getEvents(github_actions):
    try:
        x=len(github_actions[True].keys())
        getEventsFromObject(github_actions)
    except:
        getEventsFromArray(github_actions)
    

def getScripts(step):
    script= []
    nonEmpty = [i for i in re.split(r"\n+",step["run"]) if i]
    script+=nonEmpty
    return script

def convert_github_actions_to_travis(github_actions_file, travis_ci_file):
    
    global travis_ci
    global foundLang
    global foundOS

    with open(github_actions_file, 'r') as f:
        github_actions = yaml.safe_load(f)

    print(yaml.dump(github_actions)+"\n")  

    for job in github_actions["jobs"].values():
        script= []
        for step in job["steps"]:
            if "run" in step:
                travis_ci["script"] += getScripts(step)
            elif "uses" in step:
                if not foundLang:
                    getLang(step)
        if not foundOS:
            getOS(job)
    
    getBranches(github_actions)
    #getEvents(github_actions) commented this feature as it has some repo specific code and needed to me rewritten

    print(yaml.dump(travis_ci)+"\n")

    with open(travis_ci_file, 'w') as f:
        yaml.dump(travis_ci, f)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python GTConverter.py <input_github_actions_file> <output_travis_ci_file>")
        sys.exit(1)
    convert_github_actions_to_travis(sys.argv[1], sys.argv[2])
