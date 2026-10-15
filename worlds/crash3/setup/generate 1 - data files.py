# convert Region Notes.txt data into region list, entrances, and locations
region_file = open("Region Notes.txt", "r")
list_file = open("1 - region list.txt", "w")
entrances_file = open("2 - region entrances.txt", "w")
locations_file = open("3 - locations.txt", "w")

for line in region_file:
    line = line.strip()
    if line.startswith("REGION"):
        region_name = line.split(":", 1)[0].split(" ")[1]
        list_file.write(region_name + "\n")
    elif "->" in line:
        entrances_file.write(line + "\n")
    elif line.startswith("LOCATION"):
        location_data = line.split("LOCATION ", 1)[1]
        locations_file.write(location_data + "\n")
        
list_file.close()
entrances_file.close()
locations_file.close()