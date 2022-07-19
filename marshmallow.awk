#!/usr/bin/env -S gawk -f

BEGIN {
    fixer = "python marshmallow.py"
}

function correct_field(field, new_field) {
    print field "\n" |& fixer
    while ((fixer |& getline line) > 0) {
        if (line == "") {
            break
        }
        new_field = new_field line "\n"
    }
    return new_field
}

/[a-z_]+\s*=\s*(fields\.[A-Z][A-Za-z]+|[A-Za-z]+Field)\(/ && field == 0 { field=1; buffer = "" }
field == 0 {print $0}
field == 1 {
    if (index($0, "(")) {
        open = open + 1
    }
    if (index($0, ")")) {
        open = open - 1
    }
    buffer = buffer $0 "\n"
    if (open == 0) {
        field = 0
        fields[FNR] = buffer
        buffer = ""
    }
}
fields[FNR] {
    printf correct_field(fields[FNR])
}

END {
    print "\0" |& fixer
    while ((fixer |& getline line) > 0) {}
    close(fixer)
}
