"""
AI Evaluation & Dynamic Contract Generation Engine for Rojgar Setu.
Powered by Google Gemini Flash API with offline-resilient fallback knowledge banks.
Implements:
1. Dynamic 4-6 Scenario MCQs across 1 to 4 vocational trades (<1s)
2. Dynamic Trade-Specific Pre-Signed Contract synthesis
3. AI Profile Bio generator
"""

import os
import json
import requests
from django.conf import settings

GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = getattr(settings, 'GEMINI_MODEL', 'gemini-flash-latest') or os.getenv('GEMINI_MODEL', 'gemini-flash-latest')

# Fallback Comprehensive Question Bank in Hindi
FALLBACK_TRADE_QUESTIONS_HI = {
    "Electrician": [
        {
            "category": "Electrician",
            "question": "घरेलू वायरिंग में स्विच हमेशा किस तार (wire) पर लगाना चाहिए?",
            "options": ["फेज़ वायर (Phase / Live)", "न्यूट्रल वायर (Neutral)", "अर्थिंग वायर (Earth)", "किसी भी तार पर"],
            "correct_option_index": 0,
            "explanation": "सुरक्षा के लिए स्विच हमेशा फेज़ तार पर लगाना चाहिए ताकि स्विच बंद होने पर उपकरण में करंट न रहे।"
        },
        {
            "category": "Electrician",
            "question": "यदि किसी घर की 16A MCB बार-बार ट्रिप कर रही है, तो प्राथमिक जांच क्या होनी चाहिए?",
            "options": ["MCB बदल दें", "लाइन में ओवरलोड या शॉर्ट-सर्किट जांचें", "अर्थिंग तार काट दें", "मोटा तार बांध दें"],
            "correct_option_index": 1,
            "explanation": "MCB ओवरलोड या शॉर्ट-सर्किट की स्थिति में सुरक्षा के लिए स्वतः बंद हो जाती है।"
        }
    ],
    "Plumber": [
        {
            "category": "Plumber",
            "question": "CPVC पाइप और PVC पाइप में मुख्य अंतर क्या है?",
            "options": ["CPVC केवल ठंडे पानी के लिए है", "CPVC गर्म और ठंडे दोनों पानी के उच्च तापमान को झेल सकता है", "PVC मजबूत होता है", "दोनों समान हैं"],
            "correct_option_index": 1,
            "explanation": "CPVC पाइप गर्म और ठंडे पानी की लाइनों के लिए विशेष रूप से उपयुक्त होता है।"
        },
        {
            "category": "Plumber",
            "question": "वॉटर पाइपलाइन में टेफ्लॉन टेप (Teflon Tape) लगाने की सही दिशा क्या होती है?",
            "options": ["चूड़ियों (Threads) के घूमने की दिशा में (Clockwise)", "उल्टी दिशा में (Anti-clockwise)", "किसी भी दिशा में", "टेप की आवश्यकता नहीं"],
            "correct_option_index": 0,
            "explanation": "चूड़ियों के क्लॉकवाइज़ दिशा में लपेटने से कसते समय टेप नहीं खुलता।"
        }
    ],
    "House Maid": [
        {
            "category": "House Maid",
            "question": "मार्बल के फर्श पर सफाई करते समय किस प्रकार के क्लीनर का उपयोग कभी नहीं करना चाहिए?",
            "options": ["सादा पानी और माइल्ड फिनाइल", "एसिड (Acid) या तेज़ाब-आधारित क्लीनर", "माइक्रोफाइबर मॉप", "फ्लोर सोप"],
            "correct_option_index": 1,
            "explanation": "एसिड मार्बल की ऊपरी चमक को जलाकर उसे पीला और खुरदरा कर देता है।"
        },
        {
            "category": "House Maid",
            "question": "किचन में गैस स्टोव और चिमनी की गहरी चिकनाई हटाने के लिए सबसे सुरक्षित तरीका क्या है?",
            "options": ["गर्म पानी, डिशवॉश लिक्विड या बेकिंग सोडा पेस्ट", "स्टील वूल से ज़ोर से रगड़ना", "पेट्रोल का उपयोग", "ब्लीच छिड़कना"],
            "correct_option_index": 0,
            "explanation": "गर्म पानी और बेकिंग सोडा सुरक्षित रूप से चिकनाई हटाते हैं बिना सतह खरोंचे।"
        }
    ],
    "Cook": [
        {
            "category": "Cook",
            "question": "खाना पकाने से पहले और बाद में स्वच्छता (Food Hygiene) का पहला नियम क्या है?",
            "options": ["हाथों को 20 सेकंड तक साबुन से धोना और एप्रन पहनना", "बर्तन में पानी भरकर रखना", "केवल गीले कपड़े से पोंछना", "तेल गर्म करना"],
            "correct_option_index": 0,
            "explanation": "भोजन की सुरक्षा और स्वच्छता के लिए हाथों का पूरी तरह स्वच्छ होना अनिवार्य है।"
        },
        {
            "category": "Cook",
            "question": "कच्ची सब्जियां और कच्चा मीट/पनीर काटते समय क्रॉस-कंटैमिनेशन रोकने का सबसे अच्छा तरीका क्या है?",
            "options": ["एक ही कटिंग बोर्ड का तुरंत उपयोग करना", "सब्जियों और कच्चे सामान के लिए अलग-अलग चॉपिंग बोर्ड व चाकू का उपयोग", "चाकू को सूखे कपड़े से पोंछना", "ठंडे पानी से धोना"],
            "correct_option_index": 1,
            "explanation": "अलग-अलग कटिंग बोर्ड से बैक्टीरिया का फैलाव रुकता है।"
        }
    ],
    "Carpenter": [
        {
            "category": "Carpenter",
            "question": "प्लाईवुड के किनारों पर एज-बेंडिंग टेप (Edge Banding Tape) लगाने का मुख्य उद्देश्य क्या है?",
            "options": ["प्लाईवुड को नमी और पानी से बचाना तथा सुंदर फिनिश देना", "वजन घटाना", "सस्ता बनाना", "रंग बदलना"],
            "correct_option_index": 0,
            "explanation": "एज-बेंडिंग टेप नमी को अंदर जाने से रोकता है और फर्नीचर को फिनिश लुक देता है।"
        },
        {
            "category": "Carpenter",
            "question": "हार्डवुड (सागवान/शीशम) में पेंच कसते समय लकड़ी को फटने से बचाने के लिए क्या करना चाहिए?",
            "options": ["पेंच पर सीधे हथौड़ा मारना", "पेंच लगाने से पहले हल्का पायलट होल (Pilot Hole) ड्रिल करना", "बड़ा पेंच उपयोग करना", "पेंच पर तेल लगाना"],
            "correct_option_index": 1,
            "explanation": "पायलट होल लकड़ी के तनाव को कम करता है जिससे लकड़ी फटने से बचती है।"
        }
    ],
    "Painter": [
        {
            "category": "Painter",
            "question": "सीलन वाली दीवार पर सीधे पेंट करने से पहले क्या करना आवश्यक है?",
            "options": ["सीधे गहरा पेंट कर दें", "सीलन का स्रोत ठीक करें, वॉल पुट्टी और वॉटरप्रूफिंग प्राइमर लगाएं", "केवल पेपर चिपकाएं", "गीला ही पेंट करें"],
            "correct_option_index": 1,
            "explanation": "बिना वॉटरप्रूफिंग के पेंट कुछ ही दिनों में पपड़ी बनकर छूट जाता है।"
        },
        {
            "category": "Painter",
            "question": "प्राइमर और फाइनल पेंट कोट के बीच हल्की सैंडिंग (घिसाई) क्यों की जाती है?",
            "options": ["पेंट उतारने के लिए", "सतह को चिकना करने और पेंट की पकड़ मजबूत बनाने के लिए", "रंग बदलने के लिए", "सैंडिंग की जरूरत नहीं होती"],
            "correct_option_index": 1,
            "explanation": "हल्की घिसाई से सतह पर धूल-कण हटते हैं और पेंट का अगला कोट मजबूती से चिपकता है।"
        }
    ],
    "Mechanic": [
        {
            "category": "Mechanic",
            "question": "टू-व्हीलर या कार का इंजन ऑयल बदलते समय क्या सावधानी रखनी चाहिए?",
            "options": ["इंजन को पूरी तरह गर्म स्थिति में तुरंत खोलना", "इंजन ठंडा होने देना और ड्रेन बोल्ट का वॉशर/सील जांचना", "पुराने ऑयल में नया मिला देना", "ऑयल फिल्टर कभी न बदलना"],
            "correct_option_index": 1,
            "explanation": "इंजन थोड़ा ठंडा होना चाहिए ताकि जलने का खतरा न हो, और नया वॉशर लगाने से ऑयल लीकेज रुकता है।"
        },
        {
            "category": "Mechanic",
            "question": "यदि वाहन के ब्रेक दबाने पर तेज घिसने की आवाज (squeaking) आ रही है, तो संभावित कारण क्या है?",
            "options": ["ब्रेक पैड/लाइनर घिस चुके हैं", "टायर में हवा ज्यादा है", "इंजन ऑयल कम है", "पेट्रोल खराब है"],
            "correct_option_index": 0,
            "explanation": "ब्रेक शू या पैड के घिस जाने पर मेटल-टू-मेटल संपर्क से आवाज आती है।"
        }
    ],
    "Construction Worker": [
        {
            "category": "Construction Worker",
            "question": "कंक्रीट या सीमेंट मसाला मिलाते समय पानी की मात्रा का क्या प्रभाव होता है?",
            "options": ["जितना ज्यादा पानी होगा कंक्रीट उतना मजबूत होगा", "संतुलित पानी आवश्यक है; अत्यधिक पानी से कंक्रीट कमजोर हो जाता है", "पानी की कोई आवश्यकता नहीं", "केवल गर्म पानी मिलाना चाहिए"],
            "correct_option_index": 1,
            "explanation": "सीमेंट के सही रिएक्शन के लिए सही वाटर-सीमेंट रेश्यो जरूरी है, ज्यादा पानी से क्रैक और कमजोरी आती है।"
        },
        {
            "category": "Construction Worker",
            "question": "निर्माण स्थल (Site) पर काम करते समय सिर की सुरक्षा के लिए क्या पहनना अनिवार्य है?",
            "options": ["सूती साफा / गमछा", "सेफ्टी हेलमेट (Hard Hat)", "ऊनी टोपी", "कोई आवश्यकता नहीं"],
            "correct_option_index": 1,
            "explanation": "ऊंचाई से गिरने वाली ईंट, रोड़ी या औजारों से सुरक्षा के लिए सेफ्टी हेलमेट अनिवार्य सुरक्षा नियम है।"
        }
    ],
    "Gardener": [
        {
            "category": "Gardener",
            "question": "पौधों में पानी देने का सबसे उपयुक्त और सुरक्षित समय कौन सा होता है?",
            "options": ["दोपहर की तेज धूप में", "सुबह जल्दी या शाम के समय जब धूप हल्की हो", "केवल रात 12 बजे", "पानी कभी भी दे सकते हैं"],
            "correct_option_index": 1,
            "explanation": "सुबह या शाम के समय पानी देने से वाष्पीकरण कम होता है और जड़ों को पर्याप्त नमी मिलती है।"
        },
        {
            "category": "Gardener",
            "question": "गमले में मिट्टी तैयार करते समय पानी के भराव (water-logging) को रोकने के लिए क्या जरूरी है?",
            "options": ["गमले में प्लास्टिक शीट बिछाना", "गमले के नीचे जल निकासी छिद्र (Drainage Hole) और कंकड़ रखना", "मिट्टी को बहुत टाइट दबाना", "बिना छेद वाले गमले चुनना"],
            "correct_option_index": 1,
            "explanation": "ड्रेनेज होल से अतिरिक्त पानी बाहर निकल जाता है जिससे पौधे की जड़ें सड़ने से बचती हैं।"
        }
    ],
    "Driver": [
        {
            "category": "Driver",
            "question": "गीली या बारिश वाली सड़क पर गाड़ी चलाते समय फिसलने (skidding) से बचने के लिए क्या करना चाहिए?",
            "options": ["गाड़ी की गति धीमी रखें और आगे के वाहन से दोगुनी दूरी बनाए रखें", "अचानक तेज ब्रेक लगाएं", "न्यूट्रल गियर में चलाएं", "हाई बीम लाइट पर तेज चलाएं"],
            "correct_option_index": 0,
            "explanation": "गीली सड़क पर ब्रेक लगाने में अधिक दूरी लगती है, इसलिए धीमी गति और पर्याप्त दूरी सबसे सुरक्षित है।"
        },
        {
            "category": "Driver",
            "question": "सड़क पर सुरक्षित ड्राइविंग के लिए लेन बदलने (Lane Change) से पहले पहला कदम क्या होना चाहिए?",
            "options": ["हॉर्न बजाते हुए सीधे मुड़ना", "साइड मिरर देखना और टर्न इंडिकेटर देना", "गाड़ी की स्पीड बढ़ाना", "अचानक स्टीयरिंग घुमाना"],
            "correct_option_index": 1,
            "explanation": "इंडिकेटर देने और रियर-व्यू मिरर जांचने से पीछे और बगल वाले वाहनों को समय पर संकेत मिलता है।"
        }
    ]
}

# Fallback Comprehensive Question Bank in English
FALLBACK_TRADE_QUESTIONS_EN = {
    "Electrician": [
        {
            "category": "Electrician",
            "question": "In domestic electrical wiring, which wire must the switch always be connected to?",
            "options": ["Phase / Live Wire", "Neutral Wire", "Earth Ground Wire", "Any wire arbitrarily"],
            "correct_option_index": 0,
            "explanation": "For safety, the switch must isolate the live phase wire so the appliance has no voltage when switched off."
        },
        {
            "category": "Electrician",
            "question": "If a household 16A MCB repeatedly trips when an appliance is switched on, what is the primary diagnosis?",
            "options": ["Replace the MCB with a higher rating", "Check the circuit for electrical overload or a short-circuit", "Disconnect the earthing wire", "Bypass with thick copper wire"],
            "correct_option_index": 1,
            "explanation": "MCBs trip automatically to protect the electrical circuit from thermal overload or short-circuit damage."
        }
    ],
    "Plumber": [
        {
            "category": "Plumber",
            "question": "What is the primary operational advantage of CPVC pipes over standard PVC pipes?",
            "options": ["CPVC is only for cold water drainage", "CPVC can withstand both hot and cold water under high pressure and temperature", "PVC is stronger for hot water", "Both are identical"],
            "correct_option_index": 1,
            "explanation": "Chlorinated Polyvinyl Chloride (CPVC) is specifically rated for domestic hot and cold pressurized water systems."
        },
        {
            "category": "Plumber",
            "question": "In which direction should PTFE Teflon tape be wrapped around threaded plumbing fittings?",
            "options": ["In the clockwise direction of thread rotation", "In the counter-clockwise direction", "In any random direction", "No tape is necessary"],
            "correct_option_index": 0,
            "explanation": "Wrapping clockwise prevents the tape from unravelling or bunching up as the threaded fitting is tightened."
        }
    ],
    "House Maid": [
        {
            "category": "House Maid",
            "question": "When cleaning natural marble or granite flooring, which cleaning agent must NEVER be used?",
            "options": ["Diluted neutral floor cleaner and water", "Acid or harsh hydrochloric acid-based toilet cleaner", "Microfiber flat mop", "Mild liquid floor soap"],
            "correct_option_index": 1,
            "explanation": "Acid permanently etches natural calcium carbonate in marble, turning it dull, pitted, and discolored."
        },
        {
            "category": "House Maid",
            "question": "What is the safest and most effective technique to degrease kitchen stovetops and exhaust hoods?",
            "options": ["Warm water with dishwashing degreaser or baking soda paste", "Scrubbing aggressively with coarse steel wool", "Wiping with petrol / kerosene", "Spraying chlorine bleach directly"],
            "correct_option_index": 0,
            "explanation": "Warm water and mild alkaline degreasers dissolve grease cleanly without scratching surface finishes."
        }
    ],
    "Cook": [
        {
            "category": "Cook",
            "question": "What is the foremost protocol of personal food hygiene before and after food preparation?",
            "options": ["Washing hands thoroughly with soap for at least 20 seconds and wearing an apron", "Keeping pots soaked in cold water", "Wiping hands with a dry dishcloth", "Preheating the cooking oil"],
            "correct_option_index": 0,
            "explanation": "A complete 20-second handwash with soap is the gold standard for preventing bacterial food contamination."
        },
        {
            "category": "Cook",
            "question": "When prepping raw meats and fresh salad vegetables, how do you prevent cross-contamination?",
            "options": ["Use the same cutting board back-to-back immediately", "Use dedicated separate chopping boards and sanitized knives for meats and vegetables", "Wipe the knife blade with a dry towel", "Rinse with cold water only"],
            "correct_option_index": 1,
            "explanation": "Using designated separate boards prevents harmful foodborne pathogens in raw items from transferring to ready-to-eat salads."
        }
    ],
    "Carpenter": [
        {
            "category": "Carpenter",
            "question": "What is the primary function of applying edge-banding tape to exposed plywood borders?",
            "options": ["Sealing exposed inner veneer layers against moisture penetration and providing a clean finish", "Reducing furniture weight", "Making the board cheaper", "Changing wood color"],
            "correct_option_index": 0,
            "explanation": "Edge banding seals porous core veneers against ambient moisture and prevents delamination while providing a sleek edge."
        },
        {
            "category": "Carpenter",
            "question": "When driving wood screws into solid hardwood, how do you prevent the timber from splitting?",
            "options": ["Hammering the screw halfway first", "Drilling a pilot hole slightly narrower than the screw shank", "Using oversized screws", "Applying grease to the screw head"],
            "correct_option_index": 1,
            "explanation": "A pre-drilled pilot hole removes localized wood fiber tension, preventing hardwood from splitting along the grain."
        }
    ],
    "Painter": [
        {
            "category": "Painter",
            "question": "Before applying emulsion paint on a wall with moisture seepage or efflorescence, what is mandatory?",
            "options": ["Apply two dark topcoats directly over the damp patch", "Rectify the moisture source, scrape flaky plaster, and apply a waterproof sealer/primer", "Cover with wallpaper and paint over", "Paint while the wall is wet"],
            "correct_option_index": 1,
            "explanation": "Without eliminating the moisture source and using a waterproofing barrier primer, new paint will blister and peel off."
        },
        {
            "category": "Painter",
            "question": "What is the purpose of light sanding between the primer coat and finish coats?",
            "options": ["To strip off all underlying paint", "To smooth surface nibs and provide mechanical keying for coat adhesion", "To alter wall pigment", "Sanding is never recommended"],
            "correct_option_index": 1,
            "explanation": "Inter-coat sanding removes surface nibs and provides optimal mechanical grip for the final finish coat."
        }
    ],
    "Mechanic": [
        {
            "category": "Mechanic",
            "question": "What essential safety precaution must be taken when draining and replacing engine oil?",
            "options": ["Opening the drain bolt immediately after an intensive highway drive", "Allowing the engine to cool safely and inspecting the drain bolt crush washer", "Mixing fresh oil into old contaminated oil", "Never replacing the oil filter"],
            "correct_option_index": 1,
            "explanation": "Allowing the engine to cool prevents severe burns, and replacing the crush washer guarantees an oil-tight drain seal."
        },
        {
            "category": "Mechanic",
            "question": "If a vehicle produces a high-pitched metallic squeal whenever the brakes are applied, what is the cause?",
            "options": ["Worn brake pads contacting the acoustic wear indicator clip", "Excessive air pressure in tyres", "Low radiator coolant levels", "Degraded fuel"],
            "correct_option_index": 0,
            "explanation": "Brake wear indicators emit an audible squeal to alert the driver before metal backing plates score the brake disc rotor."
        }
    ],
    "Construction Worker": [
        {
            "category": "Construction Worker",
            "question": "What is the structural effect of adding excessive water into a concrete or mortar mix?",
            "options": ["It significantly increases final compressive load capacity", "It severely reduces structural strength and causes shrinkage cracking", "Water has zero effect on cured concrete strength", "It completely replaces curing"],
            "correct_option_index": 1,
            "explanation": "Surplus water evaporates leaving internal porous capillary voids that drastically reduce compressive strength."
        },
        {
            "category": "Construction Worker",
            "question": "What personal protective equipment (PPE) is strictly required on site to guard against falling objects?",
            "options": ["Cotton cloth cap / bandana", "Certified Safety Hard Hat with chinstrap", "Woolen winter cap", "No PPE required"],
            "correct_option_index": 1,
            "explanation": "Hard hats deflect and absorb kinetic impact from falling masonry, tools, and structural hazards."
        }
    ],
    "Gardener": [
        {
            "category": "Gardener",
            "question": "What is the most effective time of day to water garden plants and lawns?",
            "options": ["During peak afternoon heat and harsh direct sunlight", "Early morning or late afternoon when solar evaporation is low", "Only at midnight", "Watering time has no effect"],
            "correct_option_index": 1,
            "explanation": "Early morning watering minimizes evaporation and allows leaves to dry before nightfall, reducing fungal risks."
        },
        {
            "category": "Gardener",
            "question": "When repotting container plants, how do you prevent root rot caused by stagnant water-logging?",
            "options": ["Lining the pot bottom with a solid plastic sheet", "Ensuring unobstructed bottom drainage holes and adding a coarse gravel layer", "Compacting the potting mix as tightly as possible", "Selecting pots without holes"],
            "correct_option_index": 1,
            "explanation": "Unobstructed drainage holes allow surplus water to exit freely, ensuring root aeration and preventing fungal decay."
        }
    ],
    "Driver": [
        {
            "category": "Driver",
            "question": "When driving on rain-slicked or wet asphalt, what is the safest technique to prevent hydroplaning?",
            "options": ["Reduce driving speed and double following distance from the vehicle ahead", "Slam on emergency brakes suddenly", "Shift into neutral gear while cruising", "Drive fast with high-beam headlights"],
            "correct_option_index": 0,
            "explanation": "Wet roads significantly increase braking distances and lower tyre traction; moderate speed preserves control."
        },
        {
            "category": "Driver",
            "question": "What is the mandatory first safety step before initiating a lane change in traffic?",
            "options": ["Honking continuously and turning abruptly", "Checking rear-view and side mirrors, checking blind spots, and signalling with indicators", "Accelerating abruptly into the adjacent lane", "Turning without indicator"],
            "correct_option_index": 1,
            "explanation": "Checking mirrors and signalling early gives adjacent drivers clear notice before any lateral movement."
        }
    ]
}

# Alias for backwards compatibility
FALLBACK_TRADE_QUESTIONS = FALLBACK_TRADE_QUESTIONS_HI


def get_trade_questions_bank(language: str = "en") -> dict:
    """Returns the question bank localized to the user's selected language ('en' or 'hi')."""
    if language == "hi":
        return FALLBACK_TRADE_QUESTIONS_HI
    return FALLBACK_TRADE_QUESTIONS_EN


def generate_multi_category_assessment(categories: list[str], language: str = "hi") -> list[dict]:
    """
    Generates practical MCQs distributed across 1 to 4 chosen trades.
    Uses Gemini Flash if online; seamlessly falls back to the localized pre-seeded trade bank.
    """
    if not categories:
        categories = ["Electrician"]

    selected = categories[:4]
    lang_label = "Hindi" if language == "hi" else "English"
    bank = get_trade_questions_bank(language)

    if GEMINI_API_KEY:
        try:
            prompt = f"""
            Generate exactly 4 to 6 practical multiple-choice questions (MCQs) for evaluating a blue-collar worker in India across these trades: {', '.join(selected)}.
            Language: {lang_label}.
            Focus strictly on on-site safety, essential tools, and practical troubleshooting.
            Return STRICT JSON array only with no markdown wrapping:
            [
              {{
                "id": 1,
                "category": "{selected[0]}",
                "question": "Question text in {lang_label}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_option_index": 0,
                "explanation": "Short 1-sentence reason why"
              }}
            ]
            """
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                cleaned = raw_text.strip().replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned)
                if isinstance(data, list) and len(data) >= 3:
                    for idx, q in enumerate(data, start=1):
                        q["id"] = idx
                    return data
        except Exception as e:
            print(f"[Rojgar Setu AI Service] Note: using fallback question bank ({e})")

    # Resilient Localized Fallback Question Compilation
    compiled_questions = []
    q_id = 1
    for cat in selected:
        cat_key = next((k for k in bank if k.lower() in cat.lower()), "Electrician")
        items = bank.get(cat_key, bank["Electrician"])
        for item in items:
            compiled_questions.append({
                "id": q_id,
                "category": cat,
                "question": item["question"],
                "options": item["options"],
                "correct_option_index": item["correct_option_index"],
                "explanation": item["explanation"]
            })
            q_id += 1
            if len(compiled_questions) >= 6:
                break
        if len(compiled_questions) >= 6:
            break

    # If still under 4 questions, append general safety questions
    while len(compiled_questions) < 4:
        if language == "hi":
            compiled_questions.append({
                "id": q_id,
                "category": selected[0],
                "question": "कार्यस्थल पर काम करते समय सुरक्षा जूते और दस्ताने (Safety PPE) पहनना क्यों आवश्यक है?",
                "options": ["चोट और दुर्घटनाओं से बचाव के लिए", "केवल दिखने के लिए", "कंपनी का नियम है", "कोई लाभ नहीं"],
                "correct_option_index": 0,
                "explanation": "PPE किट अप्रत्याशित चोटों और बिजली/मशीन के खतरों से सुरक्षा प्रदान करती है।"
            })
        else:
            compiled_questions.append({
                "id": q_id,
                "category": selected[0],
                "question": "Why is wearing personal protective equipment (PPE like safety gloves and shoes) essential on work sites?",
                "options": ["To safeguard against severe workplace injuries and accidental hazards", "Merely for appearance", "Strictly an optional formality", "Provides zero benefit"],
                "correct_option_index": 0,
                "explanation": "PPE protects workers against electrical shock, sharp cuts, and blunt kinetic impacts."
            })
        q_id += 1

    return compiled_questions


def generate_dynamic_contract_terms(category: str, price: float, duration: str, tasks: str, employer_name: str = "Employer", lang: str = "en") -> str:
    """
    Generates legally structured, trade-specific dynamic contract clauses for P2P individual hiring.
    Implements 1st-Party digital stamp integration from Job Creation with pure localization.
    """
    category_upper = (category or "GENERAL WORK").upper()
    if lang == 'hi':
        return (
            f"डिजिटल प्रत्यक्ष सेवा अनुबंध ({category_upper})\n"
            f"====================================================\n"
            f"1. पक्षकार व संबंध: गृहस्वामी ({employer_name}) और स्वतंत्र कारीगर के बीच सीधा व्यक्तिगत (P2P) अनुबंध। शून्य एजेंसी व दलाली।\n"
            f"2. कार्य का दायरा: {tasks}\n"
            f"3. कार्य अवधि: {duration}\n"
            f"4. सहमत पारिश्रमिक: ₹ {float(price):,.2f} (कार्य संतोषजनक पूर्ण होने पर कारीगर को सीधे देय)।\n"
            f"5. सुरक्षा व संपत्ति सुरक्षा: कारीगर घरेलू सुरक्षा मानकों का पालन करेगा तथा संपत्ति का ध्यान रखेगा।\n"
            f"6. प्रत्यक्ष भुगतान: 100% पारिश्रमिक सीधे कारीगर को मिलेगा। शून्य प्लेटफॉर्म कटौती।\n"
            f"7. डिजिटल हस्ताक्षर मान्यता: यह अनुबंध नियोक्ता द्वारा पूर्व-हस्ताक्षरित है और चैट में कारीगर द्वारा स्वीकार करते ही कानूनी रूप से प्रभावी होगा।"
        )
    return (
        f"DYNAMIC P2P SERVICE CONTRACT FOR {category_upper}\n"
        f"====================================================\n"
        f"1. PARTIES & RELATIONSHIP: Direct Individual-to-Individual (P2P) hiring between Homeowner ({employer_name}) "
        f"and Independent Karigar. Zero recruitment agency or broker involvement.\n"
        f"2. SCOPE OF SERVICES: {tasks}\n"
        f"3. DURATION & SCHEDULE: {duration}\n"
        f"4. TOTAL AGREED COMPENSATION: INR {float(price):,.2f} payable directly to Worker upon satisfactory completion.\n"
        f"5. SAFETY & PROPERTY CARE: Worker agrees to uphold domestic safety standards and handle employer property with due care.\n"
        f"6. DIRECT SETTLEMENT: 100% of the wage is paid directly. Zero brokerage, deduction, or platform fee.\n"
        f"7. DUAL-SIGNATURE VALIDITY: This contract is pre-signed by the Employer and becomes legally binding once counter-signed by the Worker in chat."
    )


TRADE_COMPETENCIES = {
    "Driver": "safe route navigation, vehicle roadworthiness checks, defensive driving techniques, and adherence to road traffic safety regulations",
    "Electrician": "domestic electrical circuits, switchgear safety, load distribution, and short-circuit troubleshooting protocols",
    "Plumber": "domestic piping layouts (CPVC/PVC), pipeline thread sealing, leak detection, and water pressure management",
    "Cook": "hygienic food preparation, kitchen workstation sanitation, cross-contamination prevention, and safety guidelines",
    "House Maid": "domestic housekeeping, surface-safe cleaning (marble and woodwork care), and organized domestic hygiene",
    "Carpenter": "structural wood joinery, edge-banding moisture protection, precision drilling, and durable furniture assembly",
    "Painter": "surface primer preparation, wall crack-filling, moisture protection, and smooth finish application",
    "Gardener": "soil aeration, plant pruning, seasonal fertilization, and domestic garden upkeep",
    "Mechanic": "automotive mechanical troubleshooting, fluid maintenance, and preventative vehicle inspection",
    "Construction Worker": "structural masonry, safe mortar mixing ratios, scaffolding protocol, and site safety adherence",
}


def generate_worker_ai_bio(name: str, trades: list[str], score: int, total_mcqs: int, language: str = "en") -> str:
    """
    Synthesizes an authentic, personalized candidate profile description based strictly on verified inputs:
    - Selected vocational trades
    - Platform technical & safety evaluation score
    - Verified identity via DigiLocker and zero-brokerage direct hiring
    STRICTLY ZERO FALSE CLAIMS: No fabricated years of experience, no fabricated salary or past employer claims.
    """
    trades_str = ", ".join(trades) if trades else "Vocational Trades"
    score_pct = int((score / max(total_mcqs, 1)) * 100)

    # Compile authentic trade competency descriptions
    competency_list = []
    for t in (trades or ["Electrician"]):
        for key, comp in TRADE_COMPETENCIES.items():
            if key.lower() in t.lower() or t.lower() in key.lower():
                competency_list.append(comp)
                break
    if not competency_list:
        competency_list.append("trade safety protocols, tool handling, and practical on-site troubleshooting")
    comp_str = "; ".join(competency_list[:2])

    if GEMINI_API_KEY:
        try:
            prompt = f"""
            Write a genuine, authentic, and respectful professional candidate evaluation for {name}, a vocational tradesperson in India.
            Selected Trades: {trades_str}.
            Platform Safety & Technical Assessment: {score}/{total_mcqs} ({score_pct}% verified proficiency).
            Core Tested Competencies: {comp_str}.
            Language: English.

            STRICT COMPLIANCE RULES:
            1. STRICTLY FORBIDDEN: Do NOT mention or invent years of experience.
            2. STRICTLY FORBIDDEN: Do NOT mention or invent wage rates, expected salary, or past employers.
            3. Highlight only real, authentic competencies: safe equipment handling, diagnostic awareness, and prompt task readiness.
            4. Note Aadhaar verification via DigiLocker with masked contact privacy and 100% direct hiring with zero agency commission.
            5. Keep tone professional, candid, and authentic (approx 75-105 words). Return plain text only.
            """
            for model_candidate in ["gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-pro-latest"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_candidate}:generateContent?key={GEMINI_API_KEY}"
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.2}
                    }
                    resp = requests.post(url, headers=headers, json=payload, timeout=5)
                    if resp.status_code == 200:
                        raw_bio = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if len(raw_bio) > 40 and "year" not in raw_bio.lower():
                            return raw_bio
                except Exception:
                    continue
        except Exception as e:
            print(f"[AI Bio Generator] Using authentic synthesized bio ({e})")

    # Resilient Authentic Tailored Bio (100% factual, zero false claims)
    return (
        f"{name} is an Aadhaar-verified vocational artisan specializing in {trades_str}. "
        f"In Rojgar Setu's technical and safety evaluation, {name} attained a verified score of {score}/{total_mcqs} ({score_pct}% proficiency), demonstrating practical knowledge of {comp_str}. "
        f"Authenticated via DigiLocker with masked contact privacy, {name} is available for direct 1-click hiring with zero agency brokerage or middleman fees."
    )


# ==============================================================================
# 4. Context-Aware Dynamic Employer Vetting Questions (Gemini Flash + Fallback)
# ==============================================================================

def _fallback_simple_questions(category: str, lang: str = 'en'):
    """Simple, everyday fallback questions when Gemini is unavailable or times out."""
    en_bank = {
        'Driver': [
            "Do you have a valid driving licence, and have you driven in both city and highway traffic?",
            "Can you drive both manual (gear) and automatic cars?",
            "Will you be available for the full time needed without any rush?",
        ],
        'Electrician': [
            "Will you bring your own electrical tools and tester?",
            "Have you fixed main power board, inverter, or wiring issues before?",
            "Will you check the problem first and tell me before buying any new parts?",
        ],
        'Plumber': [
            "Will you bring your own plumbing tools and pipe wrench?",
            "Have you fixed wall pipe leaks and kitchen or bathroom taps before?",
            "After checking the leak, will you tell me what parts are needed before buying them?",
        ],
        'House Maid': [
            "Are you comfortable with all the work needed (sweeping, mopping, utensils, clothes)?",
            "Does this daily timing work well for you?",
            "Do you have any weekly off day preference we should decide before starting?",
        ],
        'Cook': [
            "Can you cook both veg and non-veg food (or pure veg, as needed)?",
            "How many people do you usually cook for, and what dishes are you best at?",
            "Does the morning and evening cooking time work for you?",
        ],
        'Carpenter': [
            "Will you bring your own carpentry tools (drill, saw, hammer)?",
            "Have you fixed kitchen cupboards, door locks, and hinges before?",
            "Once you see the work, can you tell me how much time it will take?",
        ],
        'Painter': [
            "Will you clean and prepare the wall properly before painting?",
            "Will you bring your own brushes, rollers, and covers to protect furniture?",
            "How many coats of paint and how much drying time will this work need?",
        ],
        'Gardener': [
            "Will you bring your own garden scissors and basic tools?",
            "Do you know how to take care of seasonal plants, grass, and plant insects?",
            "Which days and times work best for you for regular watering and care?",
        ],
        'Mechanic': [
            "Will you bring your own repair tools to check the vehicle here?",
            "Have you repaired this type of bike or car before?",
            "Will you tell me the parts cost before changing anything?",
        ],
        'Construction Worker': [
            "Have you done brick, plaster, or tile work like this before?",
            "Will you wear safety gloves and basic protection while working?",
            "Can you reach on time every day until the work finishes?",
        ],
    }
    hi_bank = {
        'Driver': [
            "क्या आपके पास पक्का ड्राइविंग लाइसेंस है और क्या आपने शहर और हाईवे दोनों जगह गाड़ी चलाई है?",
            "क्या आप गियर वाली और ऑटोमैटिक दोनों तरह की गाड़ियां चला लेते हैं?",
            "क्या आप पूरे तय समय तक बिना किसी जल्दबाजी के रुक पाएंगे?",
        ],
        'Electrician': [
            "क्या आप अपने बिजली के औजार और टेस्टर साथ लेकर आएंगे?",
            "क्या आपने पहले मेन बोर्ड, इनवर्टर और घर की वायरिंग का काम किया है?",
            "क्या आप पहले खराबी देखकर बता देंगे कि कौन सा नया सामान लाना होगा?",
        ],
        'Plumber': [
            "क्या आप अपने प्लंबिंग के औजार और पाना साथ लेकर आएंगे?",
            "क्या आपने पहले दीवार के अंदर के पाइप लीक और नल-टंकी का काम किया है?",
            "चेक करने के बाद क्या आप बता देंगे कि कौन सा सामान या फिटिंग खरीदनी है?",
        ],
        'House Maid': [
            "क्या आप झाड़ू-पोंछा, बर्तन और कपड़े धोने जैसे सभी काम आराम से कर लेंगी?",
            "क्या यह रोज़ का समय आपके आने-जाने के लिए सही है?",
            "क्या हफ्ते में छुट्टी को लेकर आपकी कोई खास बात है जो हम अभी तय कर लें?",
        ],
        'Cook': [
            "क्या आप शाकाहारी और मांसाहारी (या सिर्फ शाकाहारी, जैसी जरूरत हो) खाना बना लेते हैं?",
            "आपने आमतौर पर कितने लोगों का खाना बनाया है और कौन-सी चीज़ें सबसे अच्छी बनाते हैं?",
            "क्या सुबह और शाम के खाने का समय आपके लिए सही है?",
        ],
        'Carpenter': [
            "क्या आप अपने बढ़ई के औजार (ड्रिल, आरी, हथौड़ा) साथ लेकर आएंगे?",
            "क्या आपने पहले किचन की अलमारी, दरवाजे के लॉक और कब्जों का काम किया है?",
            "काम देखने के बाद क्या आप बता देंगे कि पूरा होने में कितना समय लगेगा?",
        ],
    }
    if lang == 'hi':
        return hi_bank.get(category, [
            "क्या आप इस काम के लिए जरूरी अपने औजार साथ लेकर आएंगे?",
            "क्या तय समय और पैसों पर आप काम शुरू करने के लिए तैयार हैं?",
            "क्या काम शुरू करने से पहले कुछ और पूछना या बताना है?",
        ])
    return en_bank.get(category, [
        "Will you bring your own tools needed for this work?",
        "Does the date, time, and payment work well for you?",
        "Is there anything else you want to ask or clarify before we finalize?",
    ])


def generate_smart_employer_questions(
    job_id: str,
    job_title: str,
    category: str,
    scope_of_work: str,
    duration_text: str,
    offered_price: float,
    recent_messages: list = None,
    lang: str = 'en',
    allow_remote_llm: bool = True,
) -> list:
    """
    Production-level context-aware question generator using Gemini Flash + Django cache.
    Understands the exact job details and live chat history to suggest all essential,
    role-specific questions an Indian homeowner should ask before sending the work agreement.
    """
    import hashlib
    from django.core.cache import cache

    recent_messages = recent_messages or []
    chat_digest = "|".join(f"{m.get('sender')}:{m.get('text')}" for m in recent_messages[-6:])
    raw_key = f"smart_q_v2:{job_id}:{lang}:{job_title}:{scope_of_work}:{chat_digest}"
    cache_key = "rs_q_" + hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    cached = cache.get(cache_key)
    if cached:
        return cached

    if allow_remote_llm and GEMINI_API_KEY and not GEMINI_API_KEY.startswith("<"):
        target_lang = "simple everyday Hindi (Devanagari script)" if lang == 'hi' else "simple everyday Indian English"
        chat_block = "\n".join(
            f"- {m.get('sender', 'User')}: {m.get('text', '')}" for m in recent_messages[-6:]
        ) or "(No messages sent yet)"

        prompt = f"""
You are helping an ordinary Indian homeowner hire a local {category} on Rojgar Setu.
Analyze the exact job and conversation below, and suggest ALL essential, practical questions the homeowner should ask the worker NEXT before signing the work agreement.
Do NOT force a fixed count of questions — include every important question needed for this specific {category} role and job situation (typically 3 to 7 questions, or fewer if some are already answered in chat).

JOB DETAILS:
- Trade: {category}
- Title: {job_title}
- Extra Details: {scope_of_work}
- Duration: {duration_text}
- Offered Pay: Rs {int(offered_price)}

RECENT CHAT MESSAGES:
{chat_block}

STRICT RULES:
1. Language: Write ONLY in {target_lang}. Keep words super simple so any local homeowner and worker in India understands immediately.
2. NO hard/technical/legal words (never use LMV, MCB, CPVC, hydraulic, compensation, commute, diagnostic, scheduled duration).
3. Understand the exact situation! If the job mentions something specific (e.g. outstation trip, elderly parents, kitchen leak, car model, night shift, multi-day work, materials), tailor the questions directly to that situation.
4. Do NOT repeat anything already asked or answered in the recent chat messages above.
5. Focus on practical essentials: safety/verification/experience, tools/parts needed, exact arrival/stay timing, specific task readiness, and extra material or overtime charges.
6. Each question must be concise (under 18 words) and polite. No fluff or filler questions.
7. Output ONLY a valid JSON array of question strings, e.g. ["Question 1?", "Question 2?", ...]. No markdown, no extra text.
"""
        models_to_try = []
        for m in ["gemini-3.8-flash-lite", "gemini-3.8-flash", GEMINI_MODEL]:
            if m and m not in models_to_try:
                models_to_try.append(m)

        for model_candidate in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_candidate}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.35},
                }
                resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=3.5)
                if resp.status_code == 200:
                    raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if raw_text.startswith("```"):
                        raw_text = raw_text.strip("`").replace("json", "", 1).strip()
                    parsed = json.loads(raw_text)
                    if isinstance(parsed, list):
                        clean_qs = [str(q).strip() for q in parsed if isinstance(q, str) and len(str(q).strip()) > 8]
                        if clean_qs:
                            cache.set(cache_key, clean_qs, timeout=1800)
                            return clean_qs
            except Exception as exc:
                print(f"[Smart Questions] Fallback ({model_candidate}): {exc}")
                continue

    # Situational & Chat-Aware Smart Fallback (0ms, works even if Gemini is 503/busy)
    combined_ctx = f"{job_title} {scope_of_work} {duration_text}".lower()
    chat_lower = " ".join(m.get("text", "").lower() for m in recent_messages)
    situational = []

    if lang == 'hi':
        if any(k in combined_ctx for k in ("parent", "elder", "hospital", "pgi", "school", "kid", "child", "माता", "पिता", "अस्पताल", "बच्च")):
            situational.append("क्या आप बुजुर्गों/परिवार के साथ आराम से और सुरक्षित तरीके से काम व मदद कर पाएंगे?")
        if any(k in combined_ctx for k in ("outstation", "highway", "trip", "tour", "delhi", "चंडीगढ़", "बाहर")):
            situational.append("क्या आप शहर से बाहर या हाईवे पर जाने के लिए तैयार हैं?")
        if any(k in combined_ctx for k in ("urgent", "today", "immediate", "तुरंत", "आज")):
            situational.append("आप आज कितनी देर में और किस समय तक पहुंच सकते हैं?")
        if any(k in combined_ctx for k in ("leak", "tap", "sink", "pipe", "लीक", "नल", "पाइप")):
            situational.append("क्या आप पहले लीकेज देखकर बता देंगे कि कौन-सी नई फिटिंग या सामान लाना होगा?")
        if any(k in combined_ctx for k in ("month", "daily", "मासिक", "रोज")):
            situational.append("क्या हफ्ते में छुट्टी और रोज़ के आने-जाने के समय को लेकर कोई बात तय करनी है?")
    else:
        if any(k in combined_ctx for k in ("parent", "elder", "hospital", "pgi", "school", "kid", "child", "family")):
            situational.append("Will you drive patiently and help my family members get in and out comfortably?")
        if any(k in combined_ctx for k in ("outstation", "highway", "trip", "tour", "days")):
            situational.append("Are you comfortable with highway driving and staying for the full trip?")
        if any(k in combined_ctx for k in ("urgent", "today", "immediate", "asap")):
            situational.append("How soon can you reach today, and can you stay until the work is done?")
        if any(k in combined_ctx for k in ("leak", "tap", "sink", "pipe", "bathroom", "kitchen")):
            situational.append("After checking the leak, will you tell me what parts are needed before buying them?")
        if any(k in combined_ctx for k in ("month", "daily", "shift")):
            situational.append("Does this daily timing suit you, and do you have any weekly off-day preference?")

    base_qs = _fallback_simple_questions(category, lang)
    merged = situational + base_qs

    # Deduplicate against topics already discussed in chat
    filtered = []
    for q in merged:
        ql = q.lower()
        if ("available" in ql or "तैयार" in ql) and ("available" in chat_lower or "तैयार" in chat_lower):
            continue
        if ("licence" in ql or "लाइसेंस" in ql) and ("licence" in chat_lower or "license" in chat_lower or "लाइसेंस" in chat_lower):
            continue
        if ("tool" in ql or "औजार" in ql) and ("tool" in chat_lower or "औजार" in chat_lower):
            continue
        if q not in filtered:
            filtered.append(q)

    final_qs = filtered or base_qs
    cache.set(cache_key, final_qs, timeout=300)
    return final_qs
