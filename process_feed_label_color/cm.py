import re

import inflect
import uvicorn
from fastapi import FastAPI
from fastapi import Request, HTTPException

app = FastAPI()


class CmRegex:
    def __init__(self, od_categories_list, fashion_homeware_od_mapping, synonyms, words_not_intended, neglect):
        self.words_not_intended = words_not_intended
        self.neglect = neglect
        self.od_categories_list = od_categories_list
        self.fashion_homeware_od_mapping = fashion_homeware_od_mapping
        self.synonyms = synonyms
        # full_categories includes od categories and their synonyms
        self.full_categories = self.od_categories_list + list(self.synonyms.keys())
        # a singular & plural converter
        self.p = inflect.engine()

    def extract_cat(self, entire_string):
        '''
        Search categories from a string, get all the matched categories.
        :param entire_string: string to be searched on
        :type entire_string: str
        :return: "Not Trendii Category", or a list of categories
        :rtype: str or list
        '''
        # Convert the string to lower case to make it case-compatible
        entire_string = entire_string.lower()
        for phrases in self.neglect:
            entire_string = entire_string.replace(phrases, '')
        # Create a dict to hold potential matches with categories
        category_dict = {}

        for category in self.full_categories:

            # Singular and plural form of the category
            # inflect module fails some cases, convert them mannually. Just need to make it work where all the categories can be converted to singular and plural.
            singular = self.p.singular_noun(category) if self.p.singular_noun(category) else category
            plural = self.p.plural(category) if not category.endswith('s') else category
            plural_exceptions = {'dress': 'dresses', 'mattress': 'mattresses', 'chest of drawer': 'chest of drawers',
                                 'wine glass': 'wine glasses', 'trousers': 'trousers', 'flip flops': 'flip flops'}
            singular_exceptions = {'dress': 'dress', 'mattress': 'mattress', 'wine glass': 'wine glass',
                                   'trousers': 'trouser', 'flip flops': 'flip flop'}
            if category in plural_exceptions:
                plural = plural_exceptions[category]
            if category in singular_exceptions:
                singular = singular_exceptions[category]

            # For "NikeSportsPants", "pants" should be matched. But for "That product is a pot", "hat" should NOT be matched.
            words_part_other_words = {'bed', 'tops', 'plant', 'clock', 'ring', 'tie', 'hat', 'seat', 'coat',
                                      'cap', 'wrap', 'suit', 'desk', 'shirt', 'pot', 'blazers', 'bag', 'mat', 'oven'}

            # if a category name is easy to be part of other words that are not category names, only match it as a whole. "hat" should match <I love hat>, <I love 'hat'>, <I love "hat"> , not <That product is a pot>
            if category in words_part_other_words:
                if re.search(rf'\b{singular}\b', entire_string) or re.search(rf'"{singular}"',
                                                                             entire_string) or re.search(
                    rf"'{singular}'", entire_string) or re.search(rf'\b{plural}\b',
                                                                  entire_string) or re.search(
                    rf'"{plural}"', entire_string) or re.search(rf"'{plural}'", entire_string):
                    canonical_category = self.synonyms.get(category, category)
                    category_dict[canonical_category] = category_dict.get(canonical_category, 0) + 1

            # Just search the category name in the string if it is not part of other words
            else:
                if re.search(singular, entire_string) or re.search(plural, entire_string):
                    if category in self.words_not_intended: return None
                    canonical_category = self.synonyms.get(category, category)
                    category_dict[canonical_category] = category_dict.get(canonical_category, 0) + 1

        if category_dict:
            # Returns the category/categories that is/are matched most times
            return [k for k, v in category_dict.items() if v == max(category_dict.values())]
        else:
            return None


# current fashion OD categories
od_categories_fashion = ["outerwear", "dress", "pants", "tops", "footwear", "shorts", "bags", "skirts", "swimwear",
                         "sunglasses", "hat", "jumpsuits", "necklace", "scarf", "earrings",
                         "belt", "gloves", "bracelet", "ring", "watch", "tie", "backpack", "handbag", "suitcase",
                         "purse"]

# current homeware OD categories
od_categories_homeware = ["bed", "nightstand", "couch", "armchair", "coffee table", "side table", "dining table",
                          "dining chair", "stool", "desk", "bookcase", "mirror",
                          "chest of drawer", "table lamp", "floor lamp", "bench", "cupboard", "flowerpot", "plant",
                          "vase", "clock", "chandelier", "office chair", "chair",
                          # v6 cates
                          'rug', 'tv', 'dishwasher',
                          'extractor', 'kettle', 'blender', 'bottle', 'coffee machine', 'rice cooker', 'spoon', 'oven',
                          'air fryer', 'wall art', 'jug', 'chopping/cutting board', 'cup', 'microwave', 'fork',
                          'bowl/basin',
                          'wine glass', 'freezer/refrigerator', 'tong', 'tea pot', 'plate', 'knife', 'toaster']

beauty_categories = ['lipstick', 'eyeshadow', 'blush']

# current fashion + homeware OD categories
od_categories_list = od_categories_fashion + od_categories_homeware + beauty_categories

# synonyms for fashion + homeware OD categories. e,g. if a feed has word "shoes" , this is feed belongs to "footwear" of OD category.
synonyms = {"night table": "nightstand", "sofa": "couch", "settee": "couch",
            "lounge chair": "armchair", "recliner": "armchair", "occasional table": "coffee table",
            "end table": "side table", "dinner table": "dining table", "kitchen table": "dining table",
            "table": "side table",
            "dining seat": "dining chair", "bookshelf": "bookcase", "shelving unit": "bookcase", "shelf": "bookcase",
            "wall mirror": "mirror", "drawer chest": "chest of drawer",
            "buffet": "chest of drawer", "lamp": "table lamp", "desk lamp": "table lamp",
            "standing lamp": "floor lamp", "closet": "cupboard", "cabinet": "cupboard", "wardrobe": "cupboard",
            "timepiece": "clock", "pendant light": "chandelier", "swivel chair": "office chair",
            "coat": "outerwear", "jacket": "outerwear", "trousers": "pants", "shirt": "tops", "shoes": "footwear",
            "boots": "footwear", "scarves": "scarf",
            "running": "footwear", "trainer": "footwear", "sandal": "footwear", "leggings": "pants",
            "joggers": "pants", "sweatshirt": "tops", "ottoman": "stool", "footrest": "stool", "footstool": "stool",
            "t-shirt": "tops", "vests": "outerwear",
            "flip flops": "footwear", "sneakers": "footwear", "blazers": "outerwear", "swimsuit": "swimwear",
            "pump": "footwear", "sweater": "tops", "bikinis": "swimwear",
            "satchel": "bags", "swimming suit": "swimwear", "cap": "hat",
            "wristband": "bracelet", "timekeeper": "watch", "necktie": "tie", "rucksack": "backpack",
            "clutch": "handbag", "luggage": "suitcase", "wallet": "purse", "jeans": "pants",
            "playsuit": "jumpsuits", "tshirt": "tops", "jumper": "tops", "blouse": "tops", "tee": "tops",
            "skort": "skirts",
            # fashion
            "cardigan": "outerwear", "suit": "outerwear", "dresser": "chest of drawer", "drawer": "chest of drawer",
            "vessel": "vase", "pot": "flowerpot", "glisteningcopper pot": "pot",
            "pedestal": "chest of drawers",
            "planter": "flowerpot", "bowl planter": "flowerpot",
            "bedframe": "bed",
            "bowl": "bowl/basin", "basin": "bowl/basin",
            "carpet": "rug", "mat": "rug", "runner rug": "rug", "tapestry": "rug", "blanket": "rug",
            "floor covering": "rug", "hearthrug": "rug",
            "television": "tv", "telly": "tv", "tube": "tv", "small screen": "tv", "boob tube": "tv", "televisor": "tv",
            "dishwashing machine": "dishwasher", "dishwasher appliance": "dishwasher",
            "automatic dishwasher": "dishwasher",
            "extracting machine": "extractor", "extractor fan": "extractor", "extractor hood": "extractor",
            "extractor tool": "extractor", "extracting device": "extractor", "extracting system": "extractor",
            "teakettle": "kettle", "boiler": "kettle", "cauldron": "kettle", "samovar": "kettle",
            "hot water pot": "kettle", "water heater": "kettle",
            "mixer": "blender", "food processor": "blender", "liquidizer": "blender",
            "flask": "bottle", "jar": "bottle", "canteen": "bottle", "decanter": "bottle", "carafe": "bottle",
            "pitcher": "bottle",
            "coffee maker": "coffee machine", "coffee brewer": "coffee machine", "espresso machine": "coffee machine",
            "coffeepot": "coffee machine",
            "coffee percolator": "coffee machine", "coffee appliance": "coffee machine",
            "cappuccino machine": "coffee machine",
            "rice steamer": "rice cooker", "rice steaming machine": "rice cooker", "rice pot": "rice cooker",
            "rice maker": "rice cooker", "rice boiling machine": "rice cooker", "rice appliance": "rice cooker",
            "ladle": "spoon", "scoop": "spoon", "dipper": "spoon", "tablespoon": "spoon", "teaspoon": "spoon",
            "stove": "oven", "cooker": "oven", "roaster": "oven",
            "oil-less fryer": "air fryer", "health fryer": "air fryer", "turbo broiler": "air fryer",
            "wall decor": "wall art", "wall hanging": "wall art", "wall ornament": "wall art", "painting": "wall art",
            "print": "wall art", "oil canvas": "wall art", "triptych": "wall art", "canvas": "wall art",
            "decanter": "jug", "ewer": "jug",
            "cutting board": "chopping/cutting board", "chopping board": "chopping/cutting board",
            "chopping block": "chopping/cutting board", "kitchen board": "chopping/cutting board",
            "cutting surface": "chopping/cutting board", "perp board": "chopping/cutting board",
            "butcher block": "chopping/cutting board",
            "carving board": "chopping/cutting board", "cooking board": "chopping/cutting board",
            "mug": "cup", "goblet": "cup", "tumbler": "cup", "chalice": "cup", "beaker": "cup", "tankard": "cup",
            "clip": "tong", "clamp": "tong", "pincer": "tong", "nipper": "tong", "gripper": "tong", "forceps": "tong",
            "tweezers": "tong", "clasp": "tong",
            "dish": "plate", "platter": "plate", "saucer": "plate", "tray": "plate", "dishware": "plate",
            "serving board": "plate",
            "toasting machine": "toaster", "toaster oven": "toaster", "bread oven": "toaster",
            "toasting appliance": "toaster", "bread broiler": "toaster",
            "cutlery set": "knife", "cutlery set": "spoon", "cutlery set": "fork",
            "teapot": "tea pot", "beer glass": "cup", "drink glasses": "cup", "champagne flutes": "wine glass",
            "water glasses": "cup", "highball glasses": "cup", "whiskey glasses": "cup", "coffee glasses": "cup",
            "shot glasses": "cup",
            "water glass": "cup", "highball glass": "cup", "whiskey glass": "cup", "coffee glass": "cup",
            "shot glass": "cup",
            "runner": "rug", "pendant": "chandelier", "lounger": "armchair", "sideboard": "nightstand",
            "wall mural": "wall art",
            "pouffe": "stool", "food chopper": "blender", "chaise lounge": "couch", "daybed": "couch",
            "lounge": "couch",
            "planter": "flowerpot", "floor light": "floor lamp", "table light": "table lamp", "martini glasses": "cup",
            "gin glasses": "cup",
            "coupe glass": "cup", "whiskey glasses": "cup", "cocktail glasses": "wine glass", "van gogh": "wall art",
            "wall hung": "wall art",
            "door mat": "rug", "back coir": "rug", "doormat": "rug", "latte glasses": "cup", "expresso glasses": "cup",
            "chair": "armchair"
            }

words_not_intended = {"glisteningcopper pot", "tv unit", "bedhead", "table cover", "wine rack", "shaving cabinet",
                      "pet bed"}

neglect = ["add to bag", "on top of", "top to bottom", "bottom to top"]

# when we got an OD category of homeware from regex, we'd love to map this category to more categories. We are doing this for importing more feeds.
homeware_od_mapping = {
    "nightstand": ["nightstand", "side table", "coffee table", "stool"],
    "side table": ["nightstand", "side table", "coffee table", "stool"],
    "coffee table": ["nightstand", "side table", "coffee table", "stool"],
    "stool": ["nightstand", "side table", "coffee table", "stool"],
    "couch": ["couch", "armchair"],
    "armchair": ["couch", "armchair", "dining chair"],
    "dining table": ["dining table", "desk", "bench"],
    "desk": ["dining table", "desk", "bench"],
    "bench": ["dining table", "desk", "bench"],
    "dining chair": ["dining chair", "armchair"],
    "bookcase": ["bookcase"],
    "bed": ["bed"],
    "flowerpot": ["flowerpot", "vase"],
    "plant": ["plant"],
    "vase": ["flowerpot", "vase"],
    "clock": ["clock"],
    "chandelier": ["chandelier"],
    "office chair": ["office chair"],
    "mirror": ["mirror"],
    "table lamp": ["table lamp"],
    "floor lamp": ["floor lamp"],
    "chest of drawer": ["chest of drawer"],
    "cupboard": ["cupboard"],
    "chair": ["armchair", "office chair", "dining chair", "couch"],
    # homeware v6
    "rug": ["rug"],
    "tv": ["tv"],
    "dishwasher": ["dishwasher"],
    "extractor": ["extractor"],
    "blender": ["blender"],
    "coffee machine": ["coffee machine"],
    "rice cooker": ["rice cooker"],
    "spoon": ["spoon"],
    "oven": ["oven"],
    "air fryer": ["air fryer"],
    "wall art": ["wall art"],
    "chopping/cutting board": ["chopping/cutting board"],
    "cup": ["cup"],
    "microwave": ["microwave"],
    "fork": ["fork"],
    "bowl/basin": ["bowl/basin"],
    "wine glass": ["wine glass"],
    "freezer/refrigerator": ["freezer/refrigerator"],
    "tong": ["tong"],
    "plate": ["plate"],
    "knife": ["knife"],
    "toaster": ["toaster"],
    "kettle": ["kettle", "pot", "tea pot"],
    "bottle": ["bottle", "jug"],
    "pot": ["kettle", "pot", "tea pot"],
    "tea pot": ["kettle", "pot", "tea pot"],
    "jug": ["bottle", "jug"],
}

# do this for fashion, same as homeware
fashion_od_mapping = {key: [key] for key in od_categories_fashion if key not in ["bags", "dress", "skirts"]}

fashion_od_mapping_plus = {"bags": ["backpack", "handbag", "suitcase", "purse", "bags"],
                           "dress": ['long_sleeve_short_dress', 'short_sleeve_short_dress', 'no_sleeve_short_dress',
                                     'long_sleeve_maxi_dress', 'short_sleeve_maxi_dress', 'no_sleeve_maxi_dress',
                                     'dress'],
                           'skirts': ['maxi_skirt', 'short_skirt', 'skirts'],
                           "handbag": ["handbag", "purse"],
                           "purse": ["handbag", "purse"]}

# combine homeware and fashion mappings
fashion_homeware_od_mapping = {**fashion_od_mapping, **fashion_od_mapping_plus, **homeware_od_mapping}

cr = CmRegex(od_categories_list, fashion_homeware_od_mapping, synonyms, words_not_intended, neglect)


