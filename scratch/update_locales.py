import json

new_keys = {
    "de": {
        "cockpit": {
            "change_practice": "\U0001f3e5 Praxis wechseln",
            "delete_case": "\U0001f5d1 Fall l\u00f6schen"
        },
        "change_practice": {
            "confirm_btn": "Praxis wechseln",
            "confirm_msg": 'Alle Kundendaten dieses Falls werden durch die Daten der neu gew\u00e4hlten Praxis "{new}" ersetzt. Fortfahren?',
            "current": "Aktuelle Praxis: {name}",
            "header": "Neue Praxis f\u00fcr diesen Fall ausw\u00e4hlen:",
            "no_customer": "Bitte eine Praxis ausw\u00e4hlen.",
            "note_label": "Notiz zum Praxiswechsel (optional):",
            "note_placeholder": "z. B. Praxis fusioniert mit...",
            "success_msg": 'Praxis wurde zu "{name}" ge\u00e4ndert.',
            "success_toast": "\u2705 Praxis ge\u00e4ndert",
            "timeline_note": 'Praxis ge\u00e4ndert von "{old}" zu "{new}".',
            "timeline_status": "PRAXIS: {old} \u2192 {new}",
            "title": "Praxis wechseln"
        },
        "delete_case": {
            "attachments_cancel_btn": "Nur Datensatz l\u00f6schen",
            "attachments_confirm_btn": "Anh\u00e4nge l\u00f6schen",
            "attachments_msg": "Soll auch der Anhang-Ordner dieses Falls gel\u00f6scht werden? ({path})",
            "attachments_title": "Anh\u00e4nge l\u00f6schen?",
            "confirm_btn": "Endg\u00fcltig l\u00f6schen",
            "confirm_msg": 'Fall "{case_id}" wird unwiderruflich gel\u00f6scht. Diese Aktion kann nicht r\u00fckg\u00e4ngig gemacht werden!',
            "confirm_title": "Fall l\u00f6schen",
            "not_found": "Fall nicht gefunden oder bereits gel\u00f6scht.",
            "success_msg": 'Fall "{case_id}" wurde gel\u00f6scht.',
            "success_toast": "\U0001f5d1 Fall gel\u00f6scht"
        },
        "dialog_titles": {
            "change_practice": "\U0001f3e5 Praxis wechseln"
        }
    },
    "en": {
        "cockpit": {
            "change_practice": "\U0001f3e5 Change Practice",
            "delete_case": "\U0001f5d1 Delete Case"
        },
        "change_practice": {
            "confirm_btn": "Change Practice",
            "confirm_msg": 'All customer data of this case will be replaced with the data of the newly selected practice "{new}". Continue?',
            "current": "Current practice: {name}",
            "header": "Select new practice for this case:",
            "no_customer": "Please select a practice.",
            "note_label": "Note about the change (optional):",
            "note_placeholder": "e.g. Practice merged with...",
            "success_msg": 'Practice was changed to "{name}".',
            "success_toast": "\u2705 Practice changed",
            "timeline_note": 'Practice changed from "{old}" to "{new}".',
            "timeline_status": "PRACTICE: {old} \u2192 {new}",
            "title": "Change Practice"
        },
        "delete_case": {
            "attachments_cancel_btn": "Only delete data record",
            "attachments_confirm_btn": "Delete attachments",
            "attachments_msg": "Should the attachment folder of this case also be deleted? ({path})",
            "attachments_title": "Delete Attachments?",
            "confirm_btn": "Delete permanently",
            "confirm_msg": 'Case "{case_id}" will be permanently deleted. This action cannot be undone!',
            "confirm_title": "Delete Case",
            "not_found": "Case not found or already deleted.",
            "success_msg": 'Case "{case_id}" was deleted.',
            "success_toast": "\U0001f5d1 Case deleted"
        },
        "dialog_titles": {
            "change_practice": "\U0001f3e5 Change Practice"
        }
    },
    "sv": {
        "cockpit": {
            "change_practice": "\U0001f3e5 Byt mottagning",
            "delete_case": "\U0001f5d1 Ta bort \u00e4rende"
        },
        "change_practice": {
            "confirm_btn": "Byt mottagning",
            "confirm_msg": 'All kunddata i detta \u00e4rende ers\u00e4tts med data fr\u00e5n den nyvalda mottagningen "{new}". Forts\u00e4tta?',
            "current": "Nuvarande mottagning: {name}",
            "header": "V\u00e4lj ny mottagning f\u00f6r detta \u00e4rende:",
            "no_customer": "V\u00e4nligen v\u00e4lj en mottagning.",
            "note_label": "Anteckning om byte (valfritt):",
            "note_placeholder": "t.ex. Mottagning sammanslagen med...",
            "success_msg": 'Mottagningen har \u00e4ndrats till "{name}".',
            "success_toast": "\u2705 Mottagning bytt",
            "timeline_note": 'Mottagning \u00e4ndrad fr\u00e5n "{old}" till "{new}".',
            "timeline_status": "MOTTAGNING: {old} \u2192 {new}",
            "title": "Byt mottagning"
        },
        "delete_case": {
            "attachments_cancel_btn": "Ta bara bort dataposten",
            "attachments_confirm_btn": "Ta bort bilagor",
            "attachments_msg": "Ska bilagemappen f\u00f6r detta \u00e4rende ocks\u00e5 tas bort? ({path})",
            "attachments_title": "Ta bort bilagor?",
            "confirm_btn": "Ta bort permanent",
            "confirm_msg": '\u00c4rende "{case_id}" tas bort permanent. Denna \u00e5tg\u00e4rd kan inte \u00e5ngras!',
            "confirm_title": "Ta bort \u00e4rende",
            "not_found": "\u00c4rendet hittades inte eller \u00e4r redan borttaget.",
            "success_msg": '\u00c4rende "{case_id}" har tagits bort.',
            "success_toast": "\U0001f5d1 \u00c4rende borttaget"
        },
        "dialog_titles": {
            "change_practice": "\U0001f3e5 Byt mottagning"
        }
    }
}

for lang, additions in new_keys.items():
    path = f"locales/{lang}.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for section, keys in additions.items():
        if section not in data:
            data[section] = {}
        for k, v in keys.items():
            data[section][k] = v
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {path}")
