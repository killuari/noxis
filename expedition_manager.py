import os, json

class ExpeditionManager:
    expeditions = {}

    @classmethod
    def load_all(cls, folder="expeditions"):
        cls.expeditions.clear()
        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                path = os.path.join(folder, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    exp_id = os.path.splitext(filename)[0]
                    cls.expeditions[exp_id] = data

                except json.JSONDecodeError as e:
                    print(f"[ERROR] Fehler in {filename}: {e}")
                except Exception as e:
                    print(f"[ERROR] Konnte {filename} nicht laden: {e}")
    
    @classmethod
    def get_expedition(cls, exp_id):
        return cls.expeditions.get(exp_id)

    def start_expedition(self, user_id, expedition_id):
        # State initialisieren, erste Event-ID starten
        pass

    def handle_event_choice(self, user_id, choice_id):
        # Nächstes Event oder Outcome ausführen
        pass

