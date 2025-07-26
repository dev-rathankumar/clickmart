# forms.py or filters.py

PRICE_CHOICES = [
    ('0-499', '0 - 499'),
    ('500-999', '500 - 999'),
    ('1000-4999', '1000 - 4999'),
    ('5000-9999', '5000 - 9999'),
    ('10000+', 'Above 10000'),
]

DISCOUNT_CHOICES = [
    ('0-9', '0 - 9% Off'),
    ('10-19', '10 - 19% Off'),
    ('20-29', '20 - 29% Off'),
    ('30-39', '30 - 39% Off'),
    ('40-49', '40 - 49% Off'),
    ('50-59', '50 - 59% Off'),
    ('60+', '60% Off or more'),
]
GENDER_CHOICES = [
    ('men', 'Men'),
    ('women', 'Women'),
    ('unisex', 'Unisex'),
    ('kids', 'Kids'),
]


GENDER_ALIAS_MAP = {
    'men': ['men', 'man', 'male','boys','boy', 'gentlemen', 'gents', 'guy', 'guys'],
    'women': ['women', 'woman', 'female', 'lady','wemen','weman','ladies', 'girl', 'girls',],
    'unisex': ['unisex','unisexed', 'unisexes', 'both', 'all','others','other'],
    'kids': ['kids', 'child', 'children', 'kid', 'childs', 'children', 'toddler', 'toddlers', 'teen', 'teens', 'youth', 'youths'],
}