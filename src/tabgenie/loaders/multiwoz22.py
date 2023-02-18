import json
from ..structs.data import Cell, Table, HFTabularDataset


def filter_empty_recursive(c):
    """Filter out empty strings, Nones, empty sequences  or dictionaries. Recursively from bottom up. Return None if
    nothing is left."""
    if isinstance(c, list):
        processed = [filter_empty_recursive(i) for i in c]
        processed = [i for i in processed if i is not None]
        processed = processed if processed else None
        return processed
    elif isinstance(c, dict):
        processed = ((k, filter_empty_recursive(v)) for k, v in c.items())
        processed = dict((k, v) for k, v in processed if v is not None)
        processed = processed if processed else None
        return processed
    elif isinstance(c, str):
        return c if c else None
    else:
        return c


def just_user_acts(turns):
    USER = 0
    SYSTEM = 1
    speakers = turns["speaker"]
    dialogue_acts = turns["dialogue_acts"]
    assert len(speakers) == len(dialogue_acts), (len(speakers), len(dialogue_acts))
    return [dai for s, dai in zip(speakers, dialogue_acts) if s == USER]


def dai2tuples(dais):
    """
    Converts dialogue act item (DAI) to linearized version

    multiwoz json format:
    "dialogue_acts": [ { "dialog_act": { "act_type": [ "Hotel-Inform" ], "act_slots": [ { "slot_name": [ "internet", "parking" ], "slot_value": [ "yes", "yes" ] },]

    linearized format:
    "dialogue_acts": [["hotel", "inform", "internet", "yes"], ["hotel", "inform", "parking", "yes"]]
    """
    for dai in dais:
        assert "dialog_act" in dai, str((dai, dais))
        d = dai["dialog_act"]
        act_types = d["act_type"]
        slots = d["act_slots"]
        slot_namess = [slot["slot_name"] for slot in slots]
        slot_valuess = [slot["slot_value"] for slot in slots]
        assert len(act_types) == len(slots), (act_types, slots)
        for act_type, slot_names, slot_values in zip(act_types, slot_namess, slot_valuess):
            assert len(slot_names) == len(slot_values), (len(slot_names), len(slot_values))
            for s, v in zip(slot_names, slot_values):
                act, act_domain = act_type.split("-")
                yield [act, act_domain, s, v]


def generate_natural_user_prompt(user_actions) -> str:
    """Source https://huggingface.co/datasets/adamlin/multiwoz_dst/blob/main/multiwoz_dst.py#L52
    TODO ask for license
    """
    user_actions.sort()

    first_attraction_inform = True
    first_hotel_inform = True
    first_restaurant_inform = True
    first_taxi_inform = True
    first_train_inform = True
    for domain, act, slot, value in user_actions:
        if domain == "Attraction":
            if act == "Inform":
                if first_attraction_inform:
                    yield "You are also looking for places to go in town."
                    first_attraction_inform = False
                if slot == "area":
                    yield f"The attraction should be in the {value}."
                elif slot == "entrancefee":
                    if value == "dontcare":
                        yield f"You do not care about the entrance fee."
                    else:
                        yield f"The entrance fee should be {value}."
                elif slot == "name":
                    yield f"You are looking for a particular attraction. Its name is called {value}."
                elif slot == "none":
                    continue
                elif slot == "type":
                    yield f"The attraction should be in the type of {value}."
                else:
                    raise ValueError(f"Unknown slot: {domain, act, slot, value}")
            elif act == "Request":
                if slot == "entrancefee":
                    yield f"Make sure you get the attraction entrance fee."
                elif slot == "parking":
                    yield f"Make sure you get the attraction parking information."
                else:
                    yield f"Make sure you get the attraction {slot}."
        elif domain == "Hospital":
            if act == "Inform":
                yield f"You are looking for {value} in Addenbrookes Hospital."
            elif act == "Request":
                yield f"Make sure you get the hospital {value}."
            else:
                raise ValueError(f"Unknown slot: {domain, act, slot, value}")
        elif domain == "Hotel":
            if act == "Inform":
                if first_hotel_inform:
                    yield "You are planning your trip in Cambridge. You are looking for a place to stay."
                    first_hotel_inform = False
                if slot == "area":
                    yield f"The hotel should be in the {value}."
                elif slot == "book day" or slot == "bookday":
                    if value == "dontcare":
                        yield f"You can to book it on any day."
                    else:
                        yield f"You want to book it on {value}."
                elif slot == "book people" or slot == "bookpeople":
                    yield f"You want to book it for {value} people."
                elif slot == "book stay" or slot == "bookstay":
                    if value == "dontcare":
                        yield f"You can to book it for any nights."
                    else:
                        yield f"You want to book it for {value} nights."
                elif slot == "choice":
                    pass
                elif slot == "internet":
                    if value == "dontcare":
                        yield f"You do not care about the internet."
                    elif value == "yes":
                        yield f"The hotel should have free wifi."
                    elif value == "no":
                        yield f"The hotel can have paid wifi."
                elif slot == "name":
                    yield f"You are looking for a particular hotel. Its name is called {value}."
                elif slot == "parking":
                    if value == "dontcare":
                        yield f"You do not care about the parking fee."
                    elif value == "yes" or value == "free":
                        yield f"The hotel should have free parking."
                    elif value == "no":
                        yield f"The hotel can have paid parking."
                elif slot == "pricerange":
                    if value == "dontcare":
                        yield "You don't care about the hotel price range."
                    else:
                        yield f"The hotel should be in the {value} price range."
                elif slot == "stars":
                    if value == "dontcare":
                        yield "You don't care about the hotel stars."
                    else:
                        yield f"The hotel should be in the {value} stars."
                elif slot == "type":
                    if value == "dontcare":
                        yield "You don't care about the hotel type."
                    else:
                        yield f"The hotel should be in the type of {value}."
                elif slot == "none":
                    continue
                else:
                    raise ValueError(f"Unknown slot: {domain, act, slot, value}")
            elif act == "Request":
                if slot == "internet":
                    yield f"Make sure you get the hotel internet information."
                elif slot == "parking":
                    yield f"Make sure you get the hotel parking information."
                elif slot == "pricerange":
                    yield f"Make sure you get the hotel price range."
                elif slot == "ref":
                    yield f"Make sure you get the hotel booking reference number."
                else:
                    yield f"Make sure you get the hotel {slot}."
        elif domain == "Police":
            if act == "Request":
                yield f"Make sure you get the police station {slot}."
        elif domain == "Restaurant":
            if act == "Inform":
                if first_restaurant_inform:
                    yield "You are traveling to Cambridge and looking forward to try local restaurants."
                    first_restaurant_inform = False
                if slot == "area":
                    yield f"The restaurant should be in the {value}."
                elif slot == "book day" or slot == "bookday":
                    if value == "dontcare":
                        yield f"You can to book it on any day."
                    else:
                        yield f"You want to book it on {value}."
                elif slot == "book people" or slot == "bookpeople":
                    yield f"You want to book it for {value} people."
                elif slot == "book time" or slot == "booktime":
                    yield f"You want to book it at {value}."
                elif slot == "food":
                    yield f"The restaurant should serve {value} food."
                elif slot == "none":
                    pass
                elif slot == "name":
                    yield f"You are looking for a particular restaurant. Its name is called {value}."
                elif slot == "pricerange":
                    if value == "dontcare":
                        yield "You don't care about the restaurant price range."
                    else:
                        yield f"The restaurant should be in the {value} price range."
                else:
                    raise ValueError(f"Unknown slot: {domain, act, slot, value}")
            elif act == "Request":
                if slot == "pricerange":
                    yield f"Make sure you get the restaurant price range."
                elif slot == "ref":
                    yield f"Make sure you get the restaurant booking reference number."
                else:
                    yield f"Make sure you get the restaurant {slot}."
        elif domain == "Taxi":
            if act == "Inform":
                if first_taxi_inform:
                    yield "You want to book a taxi."
                    first_taxi_inform = False
                if slot == "arriveby":
                    yield f"The taxi should arrive by {value}."
                elif slot == "book people" or slot == "bookpeople":
                    yield f"You want to book it for {value} people."
                elif slot == "departure":
                    yield f"The taxi should depart from {value}."
                elif slot == "destination":
                    yield f"The taxi should go to {value}."
                elif slot == "leaveat":
                    yield f"The taxi should leave at {value}."
                elif slot == "none":
                    pass
                else:
                    raise ValueError(f"Unknown slot: {domain, act, slot, value}")
            elif act == "Request":
                yield f"Make sure you get the taxi {slot}."
        elif domain == "Train":
            if act == "Inform":
                if first_train_inform:
                    yield "You want to book a train."
                    first_train_inform = False
                if slot == "arriveby":
                    yield f"The train should arrive by {value}."
                elif slot == "book people" or slot == "bookpeople":
                    yield f"You want to book it for {value} people."
                elif slot == "day":
                    yield f"You want to book it on {value}."
                elif slot == "departure":
                    yield f"The train should depart from {value}."
                elif slot == "destination":
                    yield f"The train should go to {value}."
                elif slot == "leaveat":
                    yield f"The train should leave at {value}."
                elif slot == "none" or slot == "price":
                    pass
                else:
                    raise ValueError(f"Unknown slot: {domain, act, slot, value}")
            elif act == "Request":
                if slot == "arriveby":
                    yield f"Make sure you get the train arrive time."
                elif slot == "duration":
                    yield f"Make sure you get the train duration."
                elif slot == "leaveat":
                    yield f"Make sure you get the train departure time."
                elif slot == "trainid":
                    yield f"Make sure you get the train id."
                elif slot == "ref":
                    yield f"Make sure you get the train booking reference number."
                else:
                    yield f"Make sure you get the train {slot}."
        elif domain == "general":
            if act == "bye":
                return "Bye"
            elif act == "greet":
                return "Greetings"
            elif act == "thank":
                return "Thank you"
        else:
            raise ValueError(f"Unknown domain: {domain}")
    return ""


class MultiWOZ22(HFTabularDataset):
    """
    The MultiWOZ 2.2 dataset: https://github.com/budzianowski/multiwoz/tree/master/data/MultiWOZ_2.2
    Is multi-domain (train, restaurant, hotel, etc) textual goal-oriented dataset."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "multi_woz_v22"
        self.name = "MultiWOZ_2.2 ref: User Goal"

    def prepare_table(self, entry):
        t = Table()
        # No reference
        t.set_generated_output("reference", "")
        t.props["dialogue_id"] = entry["dialogue_id"]
        t.props["services"] = " ".join(entry["services"])
        t.props["raw_turns"] = json.dumps(filter_empty_recursive(entry["turns"]))
        t.props["title"] = "Instructions to user"

        turns = entry["turns"]
        dialogue_acts = list(dai2tuples(just_user_acts(turns)))
        t.props["reference"] = list(generate_natural_user_prompt(dialogue_acts))

        col_names = ["turn_id", "speaker", "utterance", "frames", "dialogue_acts"]
        display_cols = ["turn_id", "speaker", "utterance"]
        column_vecs = zip(*[turns[c] for c in display_cols])

        for name in display_cols:
            t.add_cell(Cell(value=name, is_col_header=True))
        t.save_row()

        for cols in column_vecs:
            for v in cols:
                t.add_cell(Cell(value=str(v)))
            t.save_row()

        return t
