"""
Master Category-Specific Agreement Generation Engine for Rojgar Setu.
Implements:
1. Master Contract Clauses (Indian Contract Act 1872, P2P Hiring, Zero Brokerage, Dispute Resolution)
2. 8 Category-Specific Statutory & Safety Addendums:
   - Electrician
   - Plumber
   - House Maid
   - Cook
   - Carpenter
   - Painter
   - Gardener
   - Driver
3. Dynamic HTML & Canonical Plain Text Compilation
4. SHA-256 Document Hashing for Unbroken Integrity
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Dict, Any, Tuple


# ==============================================================================
# 1. Master Contractual Clauses (Applied to All Categories)
# ==============================================================================

MASTER_CLAUSES_EN = [
    {
        "clause_num": "1",
        "title": "PARTIES AND LEGAL RELATIONSHIP",
        "content": (
            "This Digital Work Agreement (the 'Agreement') constitutes a direct, legally binding contract "
            "between the Employer (Homeowner/Individual Hirer) and the Worker (Independent Vocational Artisan) "
            "governed by the Indian Contract Act, 1872. The parties expressly acknowledge that this engagement is on an "
            "independent, task-specific, individual-to-individual (P2P) basis. Nothing herein shall be construed as "
            "establishing an employment relationship, master-servant relationship, partnership, or joint venture. "
            "Rojgar Setu acts strictly as a neutral digital platform and is neither a contracting party, broker, nor labor contractor."
        )
    },
    {
        "clause_num": "2",
        "title": "SCOPE OF WORK AND MUTUAL RESPONSIBILITIES",
        "content": (
            "The Worker agrees to execute the specific tasks detailed in the Schedule of Work with professional skill, "
            "standard vocational care, and due diligence. The Employer agrees to provide necessary and safe access to the "
            "specified work area, disclose known hazards or pre-existing structural/electrical/plumbing defects, and furnish "
            "such materials or utilities as agreed prior to commencement."
        )
    },
    {
        "clause_num": "3",
        "title": "COMPENSATION AND 100% DIRECT SETTLEMENT",
        "content": (
            "The Employer shall pay the Worker the Total Agreed Compensation upon satisfactory completion of the agreed work. "
            "Zero platform commission, broker fee, or agency deduction shall be applied. Payment shall be transferred directly "
            "from Employer to Worker via cash, UPI, or direct banking upon task sign-off. Any additional work requested outside "
            "the original scope shall require prior mutual agreement on additional remuneration."
        )
    },
    {
        "clause_num": "4",
        "title": "SAFETY, PROPERTY PROTECTION, AND NON-DISCLOSURE",
        "content": (
            "Both parties agree to uphold household safety protocols. The Worker agrees to handle Employer property with care, "
            "and immediately notify the Employer of any accidental damage or unsafe site condition. The Worker shall maintain "
            "strict confidentiality regarding the Employer's private premises, personal belongings, and household affairs. "
            "The Employer guarantees a respectful, dignified, and safe working environment free of harassment or discrimination."
        )
    },
    {
        "clause_num": "5",
        "title": "DISPUTE RESOLUTION AND ESCALATION",
        "content": (
            "Any dispute or difference arising out of or in connection with this Agreement shall first be resolved through "
            "good-faith mutual consultation facilitated via Rojgar Setu's In-App Incident Management System. If unresolved, "
            "either party may seek appropriate legal recourse under the jurisdiction of the competent civil/consumer courts "
            "having territorial jurisdiction over the work site location."
        )
    },
    {
        "clause_num": "6",
        "title": "ELECTRONIC SIGNATURE AND TAMPER-EVIDENT VALIDITY",
        "content": (
            "By capturing an electronic signature, both parties consent to enter into this contract electronically under Section 10A "
            "of the Information Technology Act, 2000. This document is cryptographically fingerprinted using a SHA-256 hash. "
            "Any alteration to the underlying terms renders this document invalid unless mutually re-executed as an amendment."
        )
    }
]

MASTER_CLAUSES_HI = [
    {
        "clause_num": "1",
        "title": "पक्षकार एवं कानूनी संबंध",
        "content": (
            "यह डिजिटल कार्य अनुबंध भारतीय अनुबंध अधिनियम, 1872 के अंतर्गत नियोक्ता (गृहस्वामी) और स्वतंत्र कामगार (कारीगर) "
            "के बीच एक प्रत्यक्ष और कानूनी रूप से बाध्यकारी समझौता है। दोनों पक्ष स्वीकार करते हैं कि यह कार्य स्वतंत्र, कार्य-विशिष्ट "
            "और व्यक्तिगत (P2P) स्तर पर है। इसे नियमित रोजगार या एजेंसी संबंध नहीं माना जाएगा। रोजगार सेतु केवल एक निष्पक्ष तकनीकी "
            "मंच है और किसी भी प्रकार का दलाल या ठेकेदार नहीं है।"
        )
    },
    {
        "clause_num": "2",
        "title": "कार्य का दायरा एवं परस्पर जिम्मेदारियां",
        "content": (
            "कारीगर कार्य विवरण में उल्लिखित कार्यों को व्यावसायिक दक्षता और उचित सावधानी के साथ पूरा करेगा। नियोक्ता कार्य स्थल तक "
            "सुरक्षित पहुंच प्रदान करेगा, किसी भी पूर्व-विद्यमान खतरे या खराबी की जानकारी पहले देगा, तथा पूर्व-सहमति अनुसार आवश्यक सामग्री उपलब्ध कराएगा।"
        )
    },
    {
        "clause_num": "3",
        "title": "पारिश्रमिक एवं 100% सीधा भुगतान",
        "content": (
            "कार्य संतोषजनक पूर्ण होने पर नियोक्ता सहमत पारिश्रमिक का पूर्ण भुगतान सीधे कारीगर को करेगा। शून्य प्लेटफॉर्म कमीशन अथवा कटौती। "
            "भुगतान UPI, नकद या बैंक ट्रांसफर से सीधे कारीगर को देय होगा। मूल कार्य से अतिरिक्त किसी भी कार्य हेतु पूर्व-सहमति से अतिरिक्त पारिश्रमिक तय होगा।"
        )
    },
    {
        "clause_num": "4",
        "title": "सुरक्षा, संपत्ति सुरक्षा एवं गोपनीयता",
        "content": (
            "दोनों पक्ष घरेलू सुरक्षा मानकों का पालन करेंगे। कारीगर नियोक्ता की संपत्ति का ध्यान रखेगा तथा किसी भी आकस्मिक क्षति की सूचना तत्काल देगा। "
            "कारीगर घर की गोपनीयता और मर्यादा का पूर्ण सम्मान रखेगा। नियोक्ता कारीगर के लिए सम्मानजनक, सुरक्षित और उत्पीड़न-मुक्त वातावरण सुनिश्चित करेगा।"
        )
    },
    {
        "clause_num": "5",
        "title": "विवाद निवारण प्रक्रिया",
        "content": (
            "कार्य अथवा भुगतान से संबंधित किसी भी विवाद का प्राथमिक समाधान रोजगार सेतु के इन-ऐप विवाद निवारण मंच के माध्यम से आपसी सद्भाव से किया जाएगा। "
            "असहमति की स्थिति में सक्षम स्थानीय न्यायालय के समक्ष वैधानिक उपचार प्राप्त करने का अधिकार दोनों पक्षों को रहेगा।"
        )
    },
    {
        "clause_num": "6",
        "title": "इलेक्ट्रॉनिक हस्ताक्षर एवं डिजिटल वैधता",
        "content": (
            "सूचना प्रौद्योगिकी अधिनियम, 2000 की धारा 10A के तहत इलेक्ट्रॉनिक हस्ताक्षर कर दोनों पक्ष इस अनुबंध को कानूनी रूप से स्वीकार करते हैं। "
            "यह दस्तावेज SHA-256 क्रिप्टोग्राफिक हैश से सुरक्षित है। किसी भी अनधिकृत बदलाव की स्थिति में यह दस्तावेज अमान्य माना जाएगा।"
        )
    }
]


# ==============================================================================
# 2. Category-Specific Legal Addendums (8 Vocational Trades)
# ==============================================================================

CATEGORY_CLAUSES_EN = {
    "Electrician": [
        {
            "clause_num": "7.A",
            "title": "ELECTRICAL CIRCUIT ISOLATION AND MAINS CONTROL",
            "content": "Before beginning wiring, switchboard alteration, or fixture installation, the Electrician must formally isolate and lock out the corresponding circuit breaker (MCB) or mains supply. The Employer shall grant uninterrupted access to the main distribution panel."
        },
        {
            "clause_num": "7.B",
            "title": "INSULATION STANDARDS AND POST-REPAIR CONTINUITY TESTING",
            "content": "All joints must be insulated with BIS-standard electrical grade insulation tape or wire nuts. The Electrician shall verify neutral-earth continuity and load balance before re-energizing circuits."
        },
        {
            "clause_num": "7.C",
            "title": "EQUIPMENT AND MATERIAL RESPONSIBILITY",
            "content": "The Electrician shall bring insulated tools (rated up to 1000V), a digital multimeter/neon tester, and standard safety gear. The Employer shall provide wires, switches, conduit, or replacement parts conforming to Indian Standard specifications (IS/BIS)."
        }
    ],
    "Plumber": [
        {
            "clause_num": "7.A",
            "title": "WATER INLET ISOLATION AND PRESSURE TESTING",
            "content": "The Plumber must shut off the overhead tank control valve or sub-line stop-cock prior to pipe disassembly. Following installation or jointing (CPVC/PVC/GI), a 30-minute static pressure leak test must be executed before concealing lines."
        },
        {
            "clause_num": "7.B",
            "title": "STRUCTURAL PRECAUTIONS AND TEFLON SEALING",
            "content": "The Plumber shall apply industrial-grade Teflon thread tape on all threaded brass/metal adapters in the clockwise thread direction. Drilling or chasing into structural reinforced concrete columns or beams is strictly prohibited without explicit homeowner consent."
        },
        {
            "clause_num": "7.C",
            "title": "MATERIAL VERIFICATION AND SLAB PROTECTION",
            "content": "Replacement fixtures, valves, solvent cement, and pipes provided by either party must be verified free of cracks. The Plumber shall ensure work area water spillage is promptly drained to prevent ceiling seepage in underlying floors."
        }
    ],
    "House Maid": [
        {
            "clause_num": "7.A",
            "title": "HOUSEHOLD DUTIES SPECIFICATION AND WORKING HOURS",
            "content": "Daily domestic housekeeping duties (floor sweeping, wet mopping, dusting, utensil cleaning, or laundry) shall strictly follow the agreed daily schedule. Reasonable rest intervals of at least 15 minutes shall be respected for shifts exceeding 4 continuous hours."
        },
        {
            "clause_num": "7.B",
            "title": "SURFACE-SAFE CLEANING PRODUCT ADHERENCE",
            "content": "The Worker shall not apply undiluted acid or corrosive compounds to Italian marble, granite, or polished wooden cabinetry. The Employer shall furnish safe, non-toxic household cleaning liquids, mops, microfiber cloths, and protective rubber gloves."
        },
        {
            "clause_num": "7.C",
            "title": "DOMESTIC PRIVACY, ACCESS BOUNDARIES, AND DIGNITY",
            "content": "The Worker shall access only the designated domestic service areas and bedrooms specifically opened by the Employer for cleaning. Employer guarantees zero unlawful confinement, humane treatment, and timely monthly/daily compensation settlement."
        }
    ],
    "Cook": [
        {
            "clause_num": "7.A",
            "title": "FOOD HYGIENE AND KITCHEN WORKSTATION SANITATION",
            "content": "The Cook shall adhere to strict food safety practices: thorough handwashing with soap prior to food prep, clean kitchen aprons, hair containment, and sanitizing cutting boards between raw vegetable and poultry handling."
        },
        {
            "clause_num": "7.B",
            "title": "ALLERGY AND DIETARY RESTRICTION COMPLIANCE",
            "content": "The Employer shall furnish a written or oral list of domestic food allergies (peanuts, gluten, dairy, spices). The Cook must rigorously segregate prohibited ingredients. The Cook shall verify that expired dairy, oil, or food items are never used."
        },
        {
            "clause_num": "7.C",
            "title": "LPG GAS CYLINDER AND APPLIANCE SAFETY",
            "content": "The Cook shall verify that the LPG cylinder regulator knob or piped natural gas (PNG) valve is turned off after concluding meal sessions. Any suspected gas odor requires immediate window ventilation and stoppage of any ignition source."
        }
    ],
    "Carpenter": [
        {
            "clause_num": "7.A",
            "title": "DIMENSIONAL SPECIFICATIONS AND WOOD SEASONING",
            "content": "Furniture framing, cabinetry, or door trimming shall adhere to dimensions mutually approved on site. All timber and commercial ply must be seasoned and pre-treated against termite infestation prior to installation."
        },
        {
            "clause_num": "7.B",
            "title": "DUST CONTAINMENT AND EYE PROTECTION",
            "content": "Cutting, planing, and sanding operations shall be conducted with protective eyewear. The Carpenter shall lay protective plastic tarpaulins over adjacent flooring to contain wood shavings and fine sawdust."
        },
        {
            "clause_num": "7.C",
            "title": "FITTINGS, HARDWARE, AND EDGE-BANDING INTEGRITY",
            "content": "All hinges, telescopic channels, and locks provided by Employer shall be installed flush and plumb. Exposed raw plywood edges must be sealed with PVC edge-banding or teak beading using heat/adhesive to prevent moisture ingress."
        }
    ],
    "Painter": [
        {
            "clause_num": "7.A",
            "title": "SURFACE PREPARATION, POP CRACK FILLING, AND PRIMING",
            "content": "All surfaces must be scraped free of loose old paint, grease, and efflorescence. Wall cracks exceeding 1mm must be filled with acrylic crack filler, followed by a primer coat before applying topcoats."
        },
        {
            "clause_num": "7.B",
            "title": "NUMBER OF COATS AND PRODUCT SPECIFICATION",
            "content": "The Painter agrees to apply the agreed number of coats (standard: 1 primer + minimum 2 finish coats) adhering to recommended drying intervals. Paint cans shall remain sealed until opened on site in the Employer's presence."
        },
        {
            "clause_num": "7.C",
            "title": "FURNITURE MASKING, HEIGHT SAFETY, AND VENTILATION",
            "content": "The Painter shall mask switch plates, flooring perimeters, and furniture with plastic sheeting. Ladders and scaffolding must be secured on level ground. Adequate ventilation must be maintained during enamel/thinner application."
        }
    ],
    "Gardener": [
        {
            "clause_num": "7.A",
            "title": "HORTICULTURE SCOPE AND PLANT CARE",
            "content": "The Gardener shall carry out lawn mowing, weeding, hedge trimming, soil aeration, and seasonal pruning according to domestic garden requirements. Established ornamental plants and fruit trees must not be cut back drastically without consent."
        },
        {
            "clause_num": "7.B",
            "title": "FERTILIZER AND ORGANIC COMPOST PROTOCOLS",
            "content": "The Gardener shall utilize organic compost, neem cake, or mild chemical fertilizers strictly in prescribed dilution ratios. Toxic pesticides must be handled with gloves and mask, and stored securely out of reach of children and domestic pets."
        },
        {
            "clause_num": "7.C",
            "title": "WATER MANAGEMENT AND MACHINERY SAFETY",
            "content": "Watering shall be scheduled in morning or late evening hours to prevent root burn. Power hedge trimmers or lawnmower blades must be inspected before use and disconnected from power sources during maintenance."
        }
    ],
    "Driver": [
        {
            "clause_num": "7.A",
            "title": "DRIVING LICENCE VALIDATION AND TRAFFIC LAW ADHERENCE",
            "content": "The Driver warrants possession of a valid, unendorsed Indian Driving Licence corresponding to the vehicle class (LMV/HMV). The Driver shall strictly adhere to the Motor Vehicles Act, speed limits, lane discipline, and mandatory seatbelt usage."
        },
        {
            "clause_num": "7.B",
            "title": "ZERO TOLERANCE: INTOXICANTS AND MOBILE USE WHILE DRIVING",
            "content": "The Driver shall operate under strict zero tolerance for alcohol, narcotics, or impairment. Operating a hand-held mobile device while the vehicle is in motion is expressly prohibited. All calls must be taken only when the vehicle is safely parked."
        },
        {
            "clause_num": "7.C",
            "title": "VEHICLE CARE, FUEL LOGGING, AND ACCIDENT REPORTING",
            "content": "The Driver shall inspect engine oil, coolant, tire pressure, and brake fluid before departure. All fuel purchases must be logged with verified receipts. In the event of an accident or breakdown, the Driver must immediately notify the Employer and police authorities."
        }
    ]
}

CATEGORY_CLAUSES_HI = {
    "Electrician": [
        {
            "clause_num": "7.A",
            "title": "विद्युत परिपथ पृथक्करण (MCB नियंत्रण)",
            "content": "वायरिंग या स्विचबोर्ड के कार्य से पूर्व इलेक्ट्रीशियन मुख्य आपूर्ति (MCB/मेन स्विच) बंद करना सुनिश्चित करेगा। नियोक्ता मुख्य पैनल तक निर्बाध पहुंच प्रदान करेगा।"
        },
        {
            "clause_num": "7.B",
            "title": "इंसुलेशन मानक एवं अर्थिंग निरंतरता परीक्षण",
            "content": "सभी जोड़ों पर BIS मानक इंसुलेशन टेप लगाना अनिवार्य है। परिपथ चालू करने से पूर्व इलेक्ट्रीशियन न्यूट्रल-अर्थ निरंतरता व लोड की जांच करेगा।"
        },
        {
            "clause_num": "7.C",
            "title": "उपकरण एवं सामग्री जिम्मेदारी",
            "content": "कारीगर 1000V रेटेड सुरक्षित इंसुलेटेड औजार व टेस्टर साथ लाएगा। नियोक्ता भारतीय मानक (IS/BIS) अनुरूप स्विच, तार व सहायक सामग्री उपलब्ध कराएगा।"
        }
    ],
    "Plumber": [
        {
            "clause_num": "7.A",
            "title": "जल आपूर्ति नियंत्रण एवं दबाव परीक्षण",
            "content": "पाइपलाइन मरम्मत से पूर्व प्लंबर ओवरहेड टैंक या इनलेट वाल्व बंद करेगा। फिटिंग के उपरांत न्यूनतम 30 मिनट तक लीकेज की जांच अनिवार्य है।"
        },
        {
            "clause_num": "7.B",
            "title": "टेफ्लॉन टेप सीलिंग एवं संरचनात्मक सुरक्षा",
            "content": "सभी चूड़ीदार जोड़ों पर क्लॉकवाइज़ दिशा में उच्च गुणवत्ता टेफ्लॉन टेप लगाया जाएगा। कंक्रीट बीम या कॉलम को काटना पूर्णतः प्रतिबंधित है।"
        },
        {
            "clause_num": "7.C",
            "title": "सामग्री जांच एवं सीलन बचाव",
            "content": "प्लंबर दरार-मुक्त पाइप व सॉल्वेंट का उपयोग करेगा तथा कार्य स्थल पर पानी का जमाव तुरंत साफ करेगा ताकि नीचे की छत पर सीलन न आए।"
        }
    ],
    "House Maid": [
        {
            "clause_num": "7.A",
            "title": "घरेलू कार्य विवरण एवं समय-सारिणी",
            "content": "झाड़ू-पोछा, बर्तन, डस्टिंग या कपड़े धोने का कार्य पूर्व-निर्धारित समय-सारिणी अनुसार होगा। 4 घंटे से अधिक निरंतर कार्य पर 15 मिनट विश्राम देय होगा।"
        },
        {
            "clause_num": "7.B",
            "title": "सतह-अनुकूल क्लीनर का सुरक्षित उपयोग",
            "content": "मार्बल अथवा पॉलिश लकड़ी पर तेजाब या हानिकारक एसिड का उपयोग वर्जित है। नियोक्ता सुरक्षित फ्लोर क्लीनर व ग्लव्स उपलब्ध कराएगा।"
        },
        {
            "clause_num": "7.C",
            "title": "मर्यादा, सुरक्षित वातावरण एवं समय पर भुगतान",
            "content": "कामगार केवल निर्धारित कमरों में ही कार्य करेगा। नियोक्ता सम्मानजनक व सुरक्षित वातावरण सुनिश्चित करेगा तथा समय पर पूरा पारिश्रमिक देगा।"
        }
    ],
    "Cook": [
        {
            "clause_num": "7.A",
            "title": "खाद्य स्वच्छता एवं रसोई सफाई",
            "content": "रसोइया भोजन पकाने से पूर्व साबुन से हाथ धोएगा, साफ एप्रन पहनेगा तथा चॉपिंग बोर्ड व बर्तनों की पूर्ण स्वच्छता बनाए रखेगा।"
        },
        {
            "clause_num": "7.B",
            "title": "एलर्जी एवं आहार संबंधी नियमों का पालन",
            "content": "नियोक्ता परिवार की एलर्जी व खान-पान प्राथमिकताओं की सूची देगा। रसोइया किसी भी एक्सपायर्ड या बासी सामग्री का उपयोग नहीं करेगा।"
        },
        {
            "clause_num": "7.C",
            "title": "LPG गैस सुरक्षा व स्टोव नियंत्रण",
            "content": "खाना पकाने के उपरांत रसोइया गैस सिलेंडर का रेगुलेटर या PNG वाल्व बंद करना सुनिश्चित करेगा। गैस गंध आने पर तत्काल खिड़कियां खोलेगा।"
        }
    ],
    "Carpenter": [
        {
            "clause_num": "7.A",
            "title": "फर्नीचर माप एवं लकड़ी की गुणवत्ता",
            "content": "बढ़ई स्वीकृत माप अनुसार कार्य करेगा। उपयोग की जाने वाली प्लाईवुड अथवा लकड़ी दीमक-रोधी व सूखा होना आवश्यक है।"
        },
        {
            "clause_num": "7.B",
            "title": "धूल रोकथाम एवं सुरक्षा चश्मा",
            "content": "कटिंग व घिसाई के दौरान बढ़ई सुरक्षा चश्मा पहनेगा तथा फर्श पर प्लास्टिक शीट बिछाकर लकड़ी के बुरादे का फैलाव रोकेगा।"
        },
        {
            "clause_num": "7.C",
            "title": "हार्डवेयर फिटिंग एवं एज-बैंडिंग",
            "content": "कब्जे, चैनल व लॉक समतल फिट होंगे। खुली प्लाई के किनारों पर नमी से बचाव हेतु PVC एज-बैंडिंग या बीडिंग लगाई जाएगी।"
        }
    ],
    "Painter": [
        {
            "clause_num": "7.A",
            "title": "दीवार सतह तैयारी, पुट्टी एवं प्राइमर",
            "content": "पेंटिंग से पूर्व पुरानी पपड़ी व तेल हटाया जाएगा। 1mm से अधिक दरारों को क्रैक फिलर से भरकर 1 कोट प्राइमर लगाना अनिवार्य है।"
        },
        {
            "clause_num": "7.B",
            "title": "कोट की संख्या व पेंट की प्रामाणिकता",
            "content": "पेंटर न्यूनतम 2 फिनिशिंग कोट लगाएगा। पेंट के डिब्बे नियोक्ता की उपस्थिति में ही खोले जाएंगे।"
        },
        {
            "clause_num": "7.C",
            "title": "फर्नीचर सुरक्षा, सीढ़ी स्थिरता एवं वेंटिलेशन",
            "content": "फर्श व फर्नीचर को प्लास्टिक शीट से ढका जाएगा। सीढ़ी को स्थिर धरातल पर रखा जाएगा तथा कमरे में हवा का संचार रखा जाएगा।"
        }
    ],
    "Gardener": [
        {
            "clause_num": "7.A",
            "title": "बागवानी दायरा एवं पौधों का संरक्षण",
            "content": "माली लॉन कटाई, निराई-गुड़ाई, कटाई-छंटाई व खाद का कार्य करेगा। फलदार या स्थापित वृक्षों को बिना अनुमति नहीं काटेगा।"
        },
        {
            "clause_num": "7.B",
            "title": "जैविक खाद एवं कीटनाशक सुरक्षा",
            "content": "माली जैविक खाद या नीम-खली का उपयोग करेगा। कीटनाशक छिड़काव के दौरान मास्क व ग्लव्स पहनेगा तथा बच्चों की पहुंच से दूर रखेगा।"
        },
        {
            "clause_num": "7.C",
            "title": "जल संरक्षण एवं औजारों की सुरक्षा",
            "content": "पौधों में पानी सुबह या शाम को दिया जाएगा। मशीन या ब्लेड का उपयोग सावधानीपूर्वक किया जाएगा।"
        }
    ],
    "Driver": [
        {
            "clause_num": "7.A",
            "title": "वैध ड्राइविंग लाइसेंस एवं यातायात नियम",
            "content": "चालक के पास वैध ड्राइविंग लाइसेंस होना अनिवार्य है। चालक मोटर वाहन अधिनियम, गति सीमा और सीटबेल्ट नियमों का पालन करेगा।"
        },
        {
            "clause_num": "7.B",
            "title": "शराब/नशे से पूर्ण परहेज एवं मोबाइल पाबंदी",
            "content": "वाहन चलाते समय शराब या नशीले पदार्थों का सेवन पूर्णतः प्रतिबंधित है। गाड़ी चलाते समय मोबाइल फोन पर बात करना सख्त मना है।"
        },
        {
            "clause_num": "7.C",
            "title": "वाहन निरीक्षण, ईंधन रिकॉर्ड व दुर्घटना सूचना",
            "content": "चालक यात्रा पूर्व तेल, पानी व टायर प्रेशर जांचेगा। ईंधन रसीद नियोक्ता को देगा। दुर्घटना या खराबी पर तत्काल नियोक्ता को सूचित करेगा।"
        }
    ]
}


# ==============================================================================
# 3. Dynamic Legal Agreement Compilation & Document Hashing Engine
# ==============================================================================

def generate_agreement_number(category: str, job_id_short: str) -> str:
    """Generates unique official agreement identifier: e.g. RS-2026-PLUM-A1B2C3D4"""
    year = datetime.now().year
    cat_code = (category[:4] if category else "WORK").upper()
    return f"RS-{year}-{cat_code}-{job_id_short.upper()}"


def compile_canonical_agreement_text(
    agreement_number: str,
    employer_name: str,
    employer_phone: str,
    worker_name: str,
    worker_phone: str,
    job_title: str,
    category: str,
    scope_of_work: str,
    locality: str,
    city: str,
    offered_price: float,
    wage_period: str,
    duration_text: str,
    milestones: str = "",
    materials_responsibility: str = "",
    lang: str = "en",
    reveal_full_address: bool = False
) -> Tuple[str, str, str]:
    """
    Compiles complete multi-clause legal agreement into:
    1. Canonical Plain Text (Deterministic for SHA-256 Hashing)
    2. Document SHA-256 Hash
    3. Rendered HTML (For Multi-page PDF-style viewer)
    """
    is_hi = (lang == 'hi')
    master_clauses = MASTER_CLAUSES_HI if is_hi else MASTER_CLAUSES_EN
    cat_clauses_dict = CATEGORY_CLAUSES_HI if is_hi else CATEGORY_CLAUSES_EN
    specific_clauses = cat_clauses_dict.get(category, cat_clauses_dict.get("Electrician", []))

    # Privacy Safeguard: Mask contact numbers to prevent personal identity exposure
    def mask_contact_phone(raw_phone):
        if not raw_phone:
            return "[सुरक्षित संपर्क]" if is_hi else "[Platform Secured]"
        digits = re.sub(r'\D', '', str(raw_phone))
        if len(digits) >= 10:
            return f"+91 ******{digits[-4:]}"
        elif len(digits) >= 4:
            return f"******{digits[-4:]}"
        return "[सुरक्षित]" if is_hi else "[Secured]"

    masked_employer_phone = mask_contact_phone(employer_phone)
    masked_worker_phone = mask_contact_phone(worker_phone)

    worker_display_name = worker_name if worker_name else ("[To Be Assigned Upon Acceptance]" if not is_hi else "[कारीगर चयन के उपरांत दर्ज होगा]")
    worker_display_phone = masked_worker_phone if worker_phone else ("[Unlocks After Execution]" if not is_hi else "[अनुबंध पूर्ण होने पर अनलॉक]")

    if reveal_full_address and locality:
        display_location = f"{locality}, {city}"
    else:
        display_location = f"{city} (सटीक पता दोनों पक्षों के हस्ताक्षर पर अनलॉक)" if is_hi else f"{city} (Exact address unlocks upon mutual execution)"

    # 1. Build Canonical Plain Text
    lines = []
    lines.append("ROJGAR SETU DIGITAL WORK AGREEMENT")
    lines.append(f"AGREEMENT ID: {agreement_number}")
    lines.append(f"DATE GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("=" * 60)
    lines.append("SECTION A: CONTRACT PARTICULARS")
    lines.append(f"1. Employer Legal Name: {employer_name}")
    lines.append(f"2. Employer Contact: {masked_employer_phone} (Platform Secured)")
    lines.append(f"3. Worker Legal Name: {worker_display_name}")
    lines.append(f"4. Worker Contact: {worker_display_phone}")
    lines.append(f"5. Trade Category: {category}")
    lines.append(f"6. Job Title: {job_title}")
    lines.append(f"7. Work Site Location: {display_location}")
    lines.append(f"8. Agreed Compensation: INR {offered_price:,.2f} ({wage_period})")
    lines.append(f"9. Estimated Duration: {duration_text}")
    lines.append(f"10. Scope & Duties: {scope_of_work}")
    if milestones:
        lines.append(f"11. Payment Milestones: {milestones}")
    if materials_responsibility:
        lines.append(f"12. Material Responsibilities: {materials_responsibility}")
    lines.append("=" * 60)
    lines.append("SECTION B: GENERAL CONTRACTUAL CLAUSES")
    for cl in master_clauses:
        lines.append(f"CLAUSE {cl['clause_num']}: {cl['title']}")
        lines.append(cl['content'])
        lines.append("")
    lines.append("=" * 60)
    lines.append(f"SECTION C: OCCUPATION-SPECIFIC SCHEDULE ({category.upper()})")
    for scl in specific_clauses:
        lines.append(f"CLAUSE {scl['clause_num']}: {scl['title']}")
        lines.append(scl['content'])
        lines.append("")
    lines.append("=" * 60)
    lines.append("SECTION D: STATUTORY DECLARATION & CONSENT")
    lines.append("The parties affirm their voluntary consent to this digital agreement.")

    canonical_text = "\n".join(lines)

    # 2. Compute SHA-256 Hash of Canonical Text
    doc_hash = hashlib.sha256(canonical_text.encode('utf-8')).hexdigest()

    # 3. Build Structured HTML for the PDF-Style Multi-Page Viewer
    html_sections = []

    doc_title = "प्रत्यक्ष सेवा अनुबंध (P2P Service Agreement)" if is_hi else "DIRECT VOCATIONAL SERVICE AGREEMENT (P2P)"
    doc_subtitle = "भारतीय अनुबंध अधिनियम, 1872 एवं सूचना प्रौद्योगिकी अधिनियम, 2000 के अंतर्गत व्यक्तिगत सेवा संविदा" if is_hi else "Independent Individual-to-Individual Service Contract under the Indian Contract Act, 1872"

    html_sections.append(f"""
    <div class="legal-doc-header text-center border-b-2 border-neutral-900 pb-5 mb-6">
        <div class="flex items-center justify-between mb-3">
            <div class="text-left">
                <span class="text-sm font-black tracking-tight text-neutral-950 font-sans">ROJGAR SETU</span>
                <span class="block text-[10px] text-neutral-500 uppercase tracking-widest font-mono">Hyperlocal Workforce Legal Rails</span>
            </div>
            <div class="text-right font-mono text-[11px] text-neutral-500 font-semibold tracking-wider">
                REF: <span class="text-neutral-950 font-bold">{agreement_number}</span>
            </div>
        </div>

        <h1 class="text-xl sm:text-2xl font-black text-neutral-950 uppercase tracking-tight mt-2">{doc_title}</h1>
        <p class="text-xs text-neutral-600 mt-1 max-w-xl mx-auto">{doc_subtitle}</p>

        <div class="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-[11px] font-mono text-neutral-600 mt-3 pt-2 border-t border-neutral-200">
            <span><strong>Agreement ID:</strong> {agreement_number}</span>
            <span>&bull;</span>
            <span><strong>Trade:</strong> {category}</span>
            <span>&bull;</span>
            <span><strong>Tamper-Proof SHA-256:</strong> <code class="text-[10px] font-bold text-neutral-800">{doc_hash[:16]}...{doc_hash[-8:]}</code></span>
        </div>
    </div>

    <!-- Clean, Non-Redundant Schedule of Particulars Table -->
    <div class="mb-6">
        <h2 class="text-xs font-bold uppercase tracking-wider text-neutral-900 bg-neutral-100 p-2.5 rounded mb-3 flex items-center justify-between">
            <span>{"अनुबंध विवरण एवं पक्षकार" if is_hi else "Schedule of Particulars & Parties"}</span>
            <span class="text-[10px] text-neutral-500 font-mono font-normal">Section 1</span>
        </h2>
        <table class="w-full text-xs text-neutral-800 border-collapse border border-neutral-200">
            <tbody>
                <tr class="border-b border-neutral-200">
                    <td class="p-2.5 font-bold bg-neutral-50 w-1/4 border-r border-neutral-200">{"नियोक्ता (First Party)" if is_hi else "Employer (First Party)"}</td>
                    <td class="p-2.5 w-1/4 border-r border-neutral-200 font-medium">
                        <span class="block text-neutral-900 font-semibold">{employer_name}</span>
                        <span class="block text-[10px] text-neutral-500 font-mono mt-0.5">{masked_employer_phone}</span>
                    </td>
                    <td class="p-2.5 font-bold bg-neutral-50 w-1/4 border-r border-neutral-200">{"कारीगर (Second Party)" if is_hi else "Worker (Second Party)"}</td>
                    <td class="p-2.5 w-1/4 font-medium">
                        <span class="block text-neutral-900 font-semibold">{worker_display_name}</span>
                        <span class="block text-[10px] text-neutral-500 font-mono mt-0.5">{worker_display_phone}</span>
                    </td>
                </tr>
                <tr class="border-b border-neutral-200">
                    <td class="p-2.5 font-bold bg-neutral-50 border-r border-neutral-200">{"कार्य स्थल" if is_hi else "Work Site Location"}</td>
                    <td class="p-2.5 border-r border-neutral-200">{display_location}</td>
                    <td class="p-2.5 font-bold bg-neutral-50 border-r border-neutral-200">{"कार्य अवधि" if is_hi else "Estimated Duration"}</td>
                    <td class="p-2.5">{duration_text}</td>
                </tr>
                <tr class="border-b border-neutral-200">
                    <td class="p-2.5 font-bold bg-neutral-50 border-r border-neutral-200">{"पारिश्रमिक" if is_hi else "Agreed Compensation"}</td>
                    <td class="p-2.5 border-r border-neutral-200 font-bold text-emerald-800">₹{offered_price:,.2f} ({wage_period})</td>
                    <td class="p-2.5 font-bold bg-neutral-50 border-r border-neutral-200">{"व्यवसाय श्रेणी" if is_hi else "Vocational Trade"}</td>
                    <td class="p-2.5 font-semibold">{category}</td>
                </tr>
                <tr>
                    <td class="p-2.5 font-bold bg-neutral-50 border-r border-neutral-200">{"कार्य विवरण व दायरा" if is_hi else "Scope of Work & Tasks"}</td>
                    <td colspan="3" class="p-2.5 leading-relaxed font-medium text-neutral-900">{scope_of_work}</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Master Clauses -->
    <div class="mb-6 space-y-4">
        <h2 class="text-xs font-bold uppercase tracking-wider text-neutral-900 bg-neutral-100 p-2 rounded">
            {"सामान्य संविदात्मक शर्तें (Master Terms)" if is_hi else "General Contractual Terms (Master Clauses)"}
        </h2>
    """)

    for cl in master_clauses:
        html_sections.append(f"""
        <div class="text-xs leading-relaxed text-neutral-800">
            <h3 class="font-bold text-neutral-950 mb-1">{cl['clause_num']}. {cl['title']}</h3>
            <p class="text-neutral-700 text-justify">{cl['content']}</p>
        </div>
        """)

    # Occupation-Specific Schedule
    html_sections.append(f"""
    </div>
    <div class="mb-6 space-y-4 pt-4 border-t border-neutral-200">
        <h2 class="text-xs font-bold uppercase tracking-wider text-neutral-900 bg-neutral-100 p-2 rounded">
            {"विशिष्ट व्यवसाय अनुसूची" if is_hi else "Occupation-Specific Statutory Schedule"}: {category.upper()}
        </h2>
    """)

    for scl in specific_clauses:
        html_sections.append(f"""
        <div class="text-xs leading-relaxed text-neutral-800">
            <h3 class="font-bold text-neutral-950 mb-1">{scl['clause_num']}. {scl['title']}</h3>
            <p class="text-neutral-700 text-justify">{scl['content']}</p>
        </div>
        """)

    html_sections.append("</div>")
    rendered_html = "\n".join(html_sections)

    return canonical_text, doc_hash, rendered_html
