"""
SY-04/SY-40: seed MANEB MSCE and JCE syllabus data.

Covers:
  * 22 MSCE subjects, papers and grade descriptors (SY-04).
  * Core JCE subjects for Forms 1-2, per the MANEB / MIE JCE framework.
  * MANEB grade scale 1-9 (SY-19).
  * One current ExamSession per level.
  * Full Core-Element / Topic trees for every MSCE subject transcribed
    from 'Regulations and Syllabuses for the MSCE Examination' (MANEB, 2020),
    and a starter JCE topic tree for every core JCE subject.

Idempotent (SY: 'seeding command shall be idempotent') - uses
update_or_create throughout, so re-running never creates duplicates.

    python manage.py seed_maneb_syllabus
"""
from django.core.management.base import BaseCommand
from syllabus.models import (
    ExamSession, Subject, Paper, SyllabusTopic,
    AssessmentObjective, GradeDescriptor, ManebGradeScale,
)


# ---------------------------------------------------------------------------
# SUBJECTS  (code, name, category, is_elective, num_papers)
# ---------------------------------------------------------------------------
MSCE_SUBJECTS = [
    ('M132', 'Additional Mathematics', 'maths', True, 2),
    ('M012', 'Agriculture', 'sciences', True, 2),
    ('M021', 'Bible Knowledge', 'humanities', True, 2),
    ('M022', 'Biology', 'sciences', True, 2),
    ('M023', 'Business Studies', 'business', True, 2),
    ('M032', 'Chichewa', 'languages', False, 3),
    ('M038', 'Chemistry', 'sciences', True, 2),
    ('M034', 'Clothing and Textile', 'technical', True, 2),
    ('M039', 'Computer Studies', 'technical', True, 2),
    ('M015', 'Creative Arts', 'arts', True, 2),
    ('M052', 'English', 'languages', False, 3),
    ('M061', 'French', 'languages', True, 3),
    ('M073', 'Geography', 'humanities', True, 2),
    ('M081', 'History', 'humanities', True, 2),
    ('M082', 'Home Economics', 'technical', True, 2),
    ('M131', 'Mathematics', 'maths', False, 2),
    ('M133', 'Metalwork', 'technical', True, 2),
    ('M164', 'Physics', 'sciences', True, 2),
    ('M182', 'Religious and Moral Education', 'humanities', True, 1),
    ('M199', 'Social Affairs', 'humanities', False, 2),
    ('M201', 'Technical Drawing', 'technical', True, 2),
    ('M231', 'Woodwork', 'technical', True, 2),
]

# Core JCE subjects (Forms 1-2) per the MANEB / MIE JCE framework. The J###
# codes are placeholders following the same numeric convention as their MSCE
# counterparts so lookups stay intuitive; replace with the exact codes from
# the current MANEB centre circular before going live.
JCE_SUBJECTS = [
    ('J052', 'English', 'languages', False, 2),
    ('J032', 'Chichewa', 'languages', False, 2),
    ('J131', 'Mathematics', 'maths', False, 2),
    ('J100', 'Integrated Science', 'sciences', False, 2),
    ('J120', 'Social and Development Studies', 'humanities', False, 2),
    ('J081', 'History', 'humanities', False, 2),
    ('J073', 'Geography', 'humanities', False, 2),
    ('J182', 'Religious and Moral Education', 'humanities', False, 1),
    ('J012', 'Agriculture', 'sciences', True, 2),
    ('J023', 'Business Studies', 'business', True, 2),
    ('J082', 'Home Economics', 'technical', True, 2),
    ('J015', 'Creative Arts', 'arts', True, 2),
]


# ---------------------------------------------------------------------------
# GRADE SCALE / SESSIONS
# ---------------------------------------------------------------------------
MANEB_GRADE_SCALE = [
    (1, 'Distinction', True, 'Highest achievement'),
    (2, 'Distinction', True, ''),
    (3, 'Credit', True, ''),
    (4, 'Credit', True, ''),
    (5, 'Credit', True, ''),
    (6, 'Credit', True, ''),
    (7, 'Pass', False, ''),
    (8, 'Pass', False, ''),
    (9, 'Fail', False, 'Did not meet minimum standard'),
]

EXAM_SESSIONS = [
    ('MSCE 2025', 2025, 'MSCE'),
    ('JCE 2025', 2025, 'JCE'),
]


# ---------------------------------------------------------------------------
# TOPIC TREES
# Each subject maps to a list of groups:
#   (parent_code, parent_title, [(child_code, child_title, [objectives]), ...])
# The parent is the "Core Element" / unit; children are the individual topics.
# ---------------------------------------------------------------------------
TOPIC_TREES = {

    # ===================== MSCE =====================

    # ---- M132 Additional Mathematics (MANEB 2020 §3.3) ----
    'M132': [
        ('3.3.1', 'Functions and Graphs', [
            ('3.3.1.1', 'Functions', [
                'find images of polynomial, exponential and logarithmic functions',
                'find minimum and maximum values of quadratics by completing the square',
                'find inverses of given functions',
                'combine two functions to find composite functions',
                'sketch graphs of quadratic equations and find turning points',
            ]),
            ('3.3.1.2', 'Cartesian Geometry', [
                'find the equation of a circle and of a tangent to a circle',
                'find the centre and radius from a circle equation',
                'solve real life problems involving Cartesian geometry',
            ]),
            ('3.3.1.3', 'Graphs', [
                'determine linear laws from functions of the form y = kx^n or y = k n^x',
                'solve exponential equations using graphs',
                'interpret graphs of exponential equations',
            ]),
            ('3.3.1.4', 'Inequalities', [
                'find critical points of inequalities by factorisation and completing the square',
                'solve quadratic inequalities using graphs and tables',
                'solve inequalities involving absolute values',
                'sketch inequalities involving absolute values',
            ]),
        ]),
        ('3.3.2', 'Series', [
            ('3.3.2.1', 'Binomial Expansion', [
                "construct Pascal's Triangle for (x - y)^n",
                'compute binomial coefficients using factorials',
                'expand expressions of the form (x + y)^n for 0 < n <= 6',
            ]),
            ('3.3.2.2', 'Power Series', [
                'expand expressions in series form using sigma notation',
                'apply properties of sigma notation',
                'determine whether series are convergent or divergent',
            ]),
        ]),
        ('3.3.3', 'Trigonometry', [
            ('3.3.3.1', 'Trigonometry', [
                'calculate six trigonometric ratios in a unit circle',
                'convert angles from degrees to radians and vice versa',
                'draw and transform trigonometric graphs',
                'simplify trigonometric expressions using identities',
                'solve simple trigonometric equations for 0 <= θ <= 360°',
                'apply trigonometry to calculate areas of shapes',
            ]),
        ]),
        ('3.3.4', 'Calculus', [
            ('3.3.4.1', 'Limits', [
                'calculate limits of the form f(x) = ax^n',
            ]),
            ('3.3.4.2', 'Differentiation', [
                'find derivatives of polynomials from first principles',
                'differentiate products, quotients and composite functions',
                'determine nature of turning points',
                'calculate rates of change',
            ]),
            ('3.3.4.3', 'Integration', [
                'integrate polynomials and composite functions by substitution',
                'find the area of a plane region bounded by functions',
                'solve real life problems involving integration',
            ]),
        ]),
        ('3.3.5', 'Mechanics', [
            ('3.3.5.1', 'Vectors', [
                'add and subtract vectors in 2 or 3 dimensions',
                'calculate scalar product, modulus, unit vector and angle between vectors',
                'find the position vector of a mid-point and the line equation',
            ]),
            ('3.3.5.2', 'Matrices', [
                'calculate the determinant of 2x2 non-singular matrices',
                'find inverses of 2x2 matrices',
                'solve simultaneous equations in two unknowns',
            ]),
            ('3.3.5.3', 'Mechanics', [
                'combine a number of forces and find force in vector notation',
                'calculate impulse, momentum and projectile range',
                'solve uniformly accelerated motion and Newton\'s laws problems',
                'find coordinates and greatest height of a projectile',
            ]),
        ]),
        ('3.3.6', 'Statistics and Probability', [
            ('3.3.6.1', 'Statistics', [
                'describe methods of collecting data and sampling methods',
                'represent data by cumulative frequencies',
                'calculate range, variance and standard deviation',
            ]),
            ('3.3.6.2', 'Probability', [
                'calculate probability using the law P(A) = 1 - P(A\')',
                'calculate probabilities of non-exclusive events',
                'calculate conditional probability',
                'calculate probabilities using binomial distributions',
            ]),
        ]),
    ],

    # ---- M012 Agriculture (MANEB 2020 §4.3) ----
    'M012': [
        ('4.3.1', 'Agriculture and Environment', [
            ('4.3.1.1', 'Physical properties of soil', [
                'list physical properties of soil', 'state types of soil structure',
                'describe experiments on physical properties of soil',
            ]),
            ('4.3.1.2', 'Chemical properties of soil', [
                'list chemical properties of soil', 'describe ways of modifying soil pH',
                'explain factors affecting soil pH and nutrient status',
            ]),
            ('4.3.1.3', 'Soil degradation', [
                'define soil degradation', 'state forms and causes of soil degradation',
                'describe control measures',
            ]),
            ('4.3.1.4', 'Agriculture and climate change', [
                'list ways of dealing with climate change in agriculture',
            ]),
            ('4.3.1.5', 'Land drainage', [
                'state the meaning of land drainage', 'describe methods of land drainage',
            ]),
        ]),
        ('4.3.2', 'Agriculture Research and Technology', [
            ('4.3.2.1', 'Agricultural Development Agencies and their Services', [
                'list agricultural development agencies in Malawi',
                'describe their services',
            ]),
            ('4.3.2.2', 'Farm mechanization', [
                'define farm mechanization', 'list types of farm machinery',
                'describe safety measures and maintenance',
            ]),
            ('4.3.2.3', 'Farm power', [
                'list sources of farm power', 'explain advantages and limitations',
            ]),
            ('4.3.2.4', 'Gender and agricultural Technologies', [
                'state gender bias concepts in agricultural technology',
                'describe ways of dealing with gender bias',
            ]),
            ('4.3.2.5', 'Improved farming technologies', [
                'define improved farming technology', 'state examples',
                'explain effects on food security',
            ]),
        ]),
        ('4.3.3', 'Agricultural Economics and Farm Business Management', [
            ('4.3.3.1', 'Farm records', [
                'list types of farm records', 'prepare farm records from data',
            ]),
            ('4.3.3.2', 'Farm budgeting', [
                'define farm budgeting', 'state types of budgets', 'prepare farm budgets',
            ]),
            ('4.3.3.3', 'Farm business decision-making', [
                'state economic principles in decision-making',
                'draw and interpret law of diminishing returns',
            ]),
            ('4.3.3.4', 'Agricultural enterprise combination', [
                'state types of enterprise combination',
                'list factors to consider when selecting enterprise combinations',
            ]),
            ('4.3.3.5', 'Agricultural cooperatives', [
                'list examples of agricultural cooperatives', 'state their principles',
                'explain importance and challenges',
            ]),
            ('4.3.3.6', 'Agricultural marketing and trading', [
                'define agricultural marketing and trading terms',
                'list marketing channels in Malawi',
                'calculate marketing costs and margins',
            ]),
            ('4.3.3.7', 'Price elasticity of demand and supply', [
                'define price elasticity of demand and supply',
                'calculate price elasticity',
                'plot graphs showing different elasticities',
            ]),
        ]),
        ('4.3.4', 'Crop production', [
            ('4.3.4.1', 'Vegetative planting materials', [
                'list vegetative planting materials',
                'explain advantages and disadvantages',
                'draw and label planting materials',
            ]),
            ('4.3.4.2', 'Cropping systems', [
                'define cropping systems', 'list cropping systems',
                'explain advantages and disadvantages', 'design a crop rotation',
            ]),
            ('4.3.4.3', 'Mushroom production', [
                'list cultivated species of mushrooms',
                'explain husbandry practices for mushroom production',
            ]),
            ('4.3.4.4', 'Crop improvement', [
                'define crop improvement', 'list crop improvement activities',
                'describe elements and methods',
            ]),
            ('4.3.4.5', 'Crop processing', [
                'state the importance of crop processing', 'describe processing of crops',
            ]),
            ('4.3.4.6', 'Pasture production and utilisation', [
                'define pasture terms', 'list types of pastures',
                'describe grazing systems in pasture management',
            ]),
            ('4.3.4.7', 'Mango production', [
                'state the importance of fruits',
                'list mango varieties grown in Malawi',
                'describe husbandry practices for mango production',
            ]),
        ]),
        ('4.3.5', 'Livestock Production', [
            ('4.3.5.1', 'Livestock feeds and feeding', [
                'state classes and examples of livestock feeds',
                'list nutrients and sources', 'explain functions of nutrients',
            ]),
            ('4.3.5.2', 'Sheep and Goat production', [
                'list breeds, diseases and parasites',
                'describe signs of disease and control',
                'classify breeds according to use',
            ]),
            ('4.3.5.3', 'Cattle production', [
                'list breeds, diseases and parasites',
                'describe management practices and housing',
            ]),
            ('4.3.5.4', 'Reproductive systems of poultry and cattle', [
                'define terms used in reproduction',
                'list parts of reproductive systems',
                'describe the oestrous cycle',
                'draw reproductive systems',
            ]),
            ('4.3.5.5', 'Livestock Improvement', [
                'define livestock improvement',
                'state aims and methods of livestock improvement',
                'describe breeding systems',
            ]),
        ]),
    ],

    # ---- M021 Bible Knowledge (MANEB 2020 §5.3) ----
    'M021': [
        ('5.3.1', 'The Bible and its Divisions', [
            ('5.3.1.1', 'Uses of the Bible', [
                'explain the Bible as the inspired word of God',
                'describe the uses of the Bible',
            ]),
        ]),
        ('5.3.2', 'God in the Old Testament', [
            ('5.3.2.1', 'Prophet Isaiah - Proto-Isaiah', [
                'define the term prophet', 'state the roles of prophets',
                'narrate the call of Isaiah',
                'describe the social, religious and political sins of Israel',
                'describe the parable of the vineyard',
            ]),
            ('5.3.2.2', 'Deutero-Isaiah', [
                'state the message of comfort to God\'s people in exile',
                'describe how Israel\'s God is incomparable',
                'explain why idol worship is ridiculous',
                'narrate the Servant Songs',
            ]),
            ('5.3.2.3', 'Trito-Isaiah', [
                'explain why foreigners and castrated Jews could be saved',
                'explain why leaders are condemned',
                'narrate the good news of deliverance',
            ]),
        ]),
        ('5.3.3', 'The Gospel According to Luke', [
            ('5.3.3.1', 'Infancy narratives', [
                'narrate the birth of John the Baptist and of Jesus',
                'describe Mary\'s song of praise',
                'describe the Jewish birth rituals',
            ]),
            ('5.3.3.2', 'The Ministry of Jesus', [
                'narrate the preaching of John the Baptist',
                'describe the Baptism and temptations of Jesus',
                'narrate healings, exorcisms and miracles',
                'narrate the parables of the Good Samaritan and the Lost',
            ]),
            ('5.3.3.3', 'The Passion of Jesus Christ', [
                'explain why Judas agreed to betray Jesus',
                'narrate the Lord\'s Supper and events on Mount Olives',
                'narrate the trials, crucifixion and resurrection',
                'state what Jesus promised before His ascension',
            ]),
            ('5.3.3.4', 'The Birth of the Church', [
                'narrate Peter\'s speech in Jerusalem',
                'describe how believers received the Holy Spirit at Pentecost',
            ]),
            ('5.3.3.5', 'The Spread of the Church', [
                'narrate the healing of the lame man at the Beautiful Gate',
                'narrate the death of Stephen',
                'narrate Saul\'s conversion near Damascus',
                'narrate Paul\'s journeys and trials',
            ]),
        ]),
        ('5.3.4', 'The Relationship Between the Old and New Testaments', [
            ('5.3.4.1', 'Jesus\' fulfilment of the Old Testament', [
                'analyse the concepts of Messiah, Lord and Servant',
                'explain how Jesus fulfils these concepts',
            ]),
            ('5.3.4.2', 'Worship', [
                'describe worship as practised in the Old Testament',
                'describe worship as practised by the early Church',
            ]),
        ]),
        ('5.3.5', 'Biblical Beliefs and Practices', [
            ('5.3.5.1', 'Biblical beliefs', ['describe and explain biblical beliefs']),
            ('5.3.5.2', 'Biblical practices', [
                'identify biblical symbols',
                'explain what the Bible teaches about marriage',
            ]),
        ]),
        ('5.3.6', 'Christian approaches to contemporary issues', [
            ('5.3.6.1', 'Christianity and contemporary issues', [
                'explain roles of Christians in conserving the environment',
                'analyse Christian teachings on Church and state',
                'outline biblical teachings that prevent HIV and AIDS',
            ]),
        ]),
    ],

    # ---- M022 Biology (MANEB 2020 §6.3) ----
    'M022': [
        ('6.3.1', 'Environment', [
            ('6.3.1.1', 'Living Things and the Environment', [
                'define sampling methods',
                'list sampling methods and components of the ecosystem',
                'construct food chains, food webs and food pyramids',
                'draw and label components of nutrient cycles',
                'explain energy flow in an ecosystem',
            ]),
        ]),
        ('6.3.2', 'Plant Biology', [
            ('6.3.2.1', 'Plant Structure and Function', [
                'define diffusion, osmosis, active transport and transpiration',
                'explain adaptations of leaves for photosynthesis',
                'describe the process of photosynthesis',
                'draw and label cross sections of leaves, stems and roots',
            ]),
            ('6.3.2.2', 'Plant Responses', [
                'define the term tropism', 'list types of tropism',
                'describe experiments on different tropisms',
            ]),
        ]),
        ('6.3.3', 'Animal Biology', [
            ('6.3.3.1', 'Vertebrates and Invertebrates', [
                'list main groups of animals and invertebrates',
                'identify animals using a dichotomous key',
                'describe locomotion in birds, fish and mammals',
            ]),
        ]),
        ('6.3.4', 'Human Biology', [
            ('6.3.4.1', 'Human Digestive System', [
                'define enzyme, assimilation, deamination and transamination',
                'state the properties of enzymes',
                'explain adaptations of small intestines for absorption',
            ]),
            ('6.3.4.2', 'Human Circulatory System', [
                'state components of the lymphatic system',
                'explain functions of the circulatory system',
                'describe the blood clotting process', 'draw and label the heart',
            ]),
            ('6.3.4.3', 'Human Reproductive System', [
                'state parts of the human reproductive system',
                'list hormones involved in the menstrual cycle',
                'describe the process of giving birth', 'describe contraceptive methods',
            ]),
            ('6.3.4.4', 'Human Respiratory System', [
                'define lung capacity terms',
                'describe how breathing occurs in humans',
                'explain effects of smoking on lungs',
            ]),
            ('6.3.4.5', 'Human Excretory System', [
                'define osmo-regulation',
                'describe how the kidney works in blood filtration',
                'draw and label the human excretory system',
            ]),
            ('6.3.4.6', 'Coordination', [
                'list types of neurones',
                'define reflex action and reflex arc',
                'draw and label parts of the neurone and CNS',
            ]),
            ('6.3.4.7', 'Immunity', [
                'list examples of organ transplants and types of blood groups',
                'explain factors to consider before blood transfusion',
                'describe the ABO and Rhesus blood groups',
            ]),
            ('6.3.4.8', 'Infectious and Non-Infectious Diseases', [
                'state examples of infectious diseases caused by bacteria, viruses and fungi',
                'define cancer', 'explain the factors that increase the risk of cancer',
                'describe prevention and control of cancer',
            ]),
        ]),
        ('6.3.5', 'Genetics and Evolution', [
            ('6.3.5.1', 'Genetics', [
                'define sex linked characteristics and mutation',
                'state causes and types of variation',
                'explain the differences between meiosis and mitosis',
                'work out monohybrid crosses',
            ]),
            ('6.3.5.2', 'Evolution', [
                'define evolution, natural selection and speciation',
                'state the evidence of evolution',
                'describe how speciation occurs',
            ]),
            ('6.3.5.3', 'Biotechnology', [
                'define biotechnology and genetic engineering',
                'list examples of biotechnology in plants and animals',
                'describe the processes of genetic engineering and insulin production',
            ]),
        ]),
    ],

    # ---- M023 Business Studies (MANEB 2020 §7.3) ----
    'M023': [
        ('7.3.1', 'Trade and Aids to Trade', [
            ('7.3.1.1', 'Foreign Trade', [
                'differentiate home trade from foreign trade',
                'mention major imports and exports of Malawi',
                'explain favourable and unfavourable balance of trade',
            ]),
            ('7.3.1.2', 'Trade Documents', [
                'mention types of home and foreign trade documents',
                'state the importance of trade documents',
                'prepare different trade documents',
            ]),
            ('7.3.1.3', 'Trade', [
                'define liberalisation and globalisation',
                'describe trade protocols and economic integrations',
                'describe the roles of bodies such as MBS, MITC, MCCCI, IBAM',
            ]),
        ]),
        ('7.3.2', 'Business Organisation', [
            ('7.3.2.1', 'Non-profit Making Organisations', [
                'define non-profit making organisations and cooperatives',
                'describe main forms of cooperative societies',
            ]),
            ('7.3.2.2', 'Statutory Corporations', [
                'define privatisation',
                'mention types of statutory corporations and forms of privatisation',
                'explain advantages and disadvantages',
            ]),
        ]),
        ('7.3.3', 'Business Finance', [
            ('7.3.3.1', 'Non-bank Financial Institutions', [
                'mention sources of business finance',
                'list non-bank financial institutions in Malawi',
            ]),
            ('7.3.3.2', 'Insurance', [
                'define insurance terms', 'state different business risks',
                'explain main insurance principles',
            ]),
        ]),
        ('7.3.4', 'Production', [
            ('7.3.4.1', 'Production', [
                'define production terms', 'state production steps and types of inputs',
                'describe stock taking',
            ]),
            ('7.3.4.2', 'Production Cost', [
                'describe economies and diseconomies of scale',
                'classify fixed and variable costs',
                'calculate production costs, revenue and profits',
                'construct and interpret a break-even chart',
            ]),
        ]),
        ('7.3.5', 'Entrepreneurship', [
            ('7.3.5.1', 'Entrepreneurship', [
                'list characteristics of an entrepreneur',
                'state rewards of entrepreneurship',
            ]),
            ('7.3.5.2', 'Small Businesses', [
                'list contributions of small scale businesses to the economy',
                'explain rewards and challenges of small businesses',
            ]),
            ('7.3.5.3', 'Marketing', [
                'define marketing and marketing mix',
                'describe marketing objectives and research',
                'illustrate product life cycle',
            ]),
            ('7.3.5.4', 'Consumer Protection', [
                'list consumer protection organisations in Malawi',
                'explain rights and responsibilities of a consumer',
            ]),
            ('7.3.5.5', 'Human Resource', [
                'differentiate wages and salaries',
                'describe recruitment, selection and training',
                'prepare a pay slip',
            ]),
            ('7.3.5.6', 'Taxation', [
                'list purposes of taxation',
                'state advantages and disadvantages of direct and indirect taxes',
                'calculate PAYE, VAT, custom duty and excise duty',
            ]),
            ('7.3.5.7', 'Business Accounting', [
                'define business accounting terms',
                'differentiate assets from liabilities',
                'prepare balance sheet, trading and P&L accounts',
            ]),
        ]),
    ],

    # ---- M032 Chichewa (MANEB 2020 §9) ----
    'M032': [
        ('9.3.1', 'Chimangirizo/Kalata ndi Za Chikhalidwe cha Amalawi', [
            ('9.3.1.1', 'Chimangirizo kapena Kalata', [
                'kulemba chimangirizo kapena kalata pa nkhani zosiyanasiyana',
                'kugwiritsa ntchito makeyala a kalata yantchito ndi yamchezo',
            ]),
            ('9.3.1.2', 'Za Chikhalidwe cha Amalawi', [
                'kusonyeza kuganiza mozama poyankha mafunso a malonje',
                'kufotokoza mauthenga ndi malangizo osiyanasiyana',
            ]),
        ]),
        ('9.3.2', 'Malamulo a Chiyankhulo, Kumvetsa Nkhani ndi Kusanthula', [
            ('9.3.2.1', 'Malamulo a Chiyankhulo', [
                'kapangidwe ka mayina, afotokozi, aonjezi',
                'mitundu ya aneni ndi nthawi za aneni',
                'zizindikiro za m\'kalembedwe',
            ]),
            ('9.3.2.2', 'Kumvetsa Nkhani ndi Kusanthula Chiyankhulo', [
                'kusanthula chiyankhulo pa nkhani yoperekedwa',
                'kuzindikira mawu ofanana ndi otsutsana m\'matanthauzo',
            ]),
            ('9.3.2.3', 'Chifupikitso', [
                'kulemba chifupikitso kuchokera m\'nkhani yoperekedwa',
                'kupeza mitu ikulukulu ya nkhani',
            ]),
            ('9.3.2.4', 'Chimasuliro', [
                'kumasulira nkhani ya m\'Chingerezi m\'Chichewa',
            ]),
        ]),
        ('9.3.3', 'Nkhani Za Mchezo ndi Zolembedwa', [
            ('9.3.3.1', 'Ndakatulo ndi Nkhani Zazifupi', [
                'kufotokoza tanthauzo la ndakatulo',
                'kuzindikira zipangizo zopezeka m\'ndakatulo',
                'kufotokoza apangankhani ndi mfundo zikuluzikulu',
            ]),
            ('9.3.3.2', 'Nkhani Yaitali ndi Masewero a Zisudzo', [
                'kufotokoza tsatanetsatane wa nkhani',
                'kusiyanitsa masewero a zisudzo ndi nkhani zina',
                'kufotokoza kufunika kwa zisudzo',
            ]),
        ]),
    ],

    # ---- M038 Chemistry (MANEB 2020 §8.3) ----
    'M038': [
        ('8.3.1', 'Analytical Skills in Chemistry', [
            ('8.3.1.1', 'Experimental Techniques', [
                'state waste products from chemical reactions',
                'describe safe ways of disposing chemical wastes',
                'carry out tests on water, ions and gases',
                'design scientific investigations in Chemistry',
            ]),
        ]),
        ('8.3.2', 'Inorganic Chemistry', [
            ('8.3.2.1', 'Nitrogen, Sulphur and Phosphorous', [
                'describe sources, properties and uses of nitrogen, sulphur and phosphorus',
            ]),
        ]),
        ('8.3.3', 'Chemical Composition of Matter', [
            ('8.3.3.1', 'Chemical Bonding and Properties of Matter', [
                'define allotropy', 'state types of intermolecular forces',
                'differentiate polar and non-polar covalent compounds',
                'describe uses of metals in relation to their properties',
            ]),
        ]),
        ('8.3.4', 'Chemical Reactions', [
            ('8.3.4.1', 'Stoichiometry', [
                'define standard solution',
                'work out the relative formula mass of a compound',
                'calculate concentration, theoretical and percentage yield',
                'deduce empirical and molecular formulae',
            ]),
            ('8.3.4.2', 'Heats of Reactions', [
                'define exothermic and endothermic reactions',
                'interpret energy level diagrams',
                'calculate overall energy change using bond energies',
            ]),
            ('8.3.4.3', 'Rates of Reactions', [
                'define rate of reaction',
                'describe factors affecting rates of reactions',
                'plot and interpret volume/mass-time graphs',
            ]),
            ('8.3.4.4', 'Acids and Bases', [
                'define acids and bases according to L/B theory',
                'classify oxides as acidic, basic or amphoteric',
                'design ways of preparing and purifying salts',
            ]),
            ('8.3.4.5', 'Oxidation-Reduction Reaction', [
                'define oxidation, reduction, reducing and oxidising agents',
                'write balanced half and overall redox equations',
                'calculate potential difference using voltage series',
            ]),
            ('8.3.4.6', 'Electrolysis', [
                'explain products of electrolysis of molten and aqueous ionic compounds',
                'describe purification of copper',
                'write balanced half and overall electrolytic equations',
            ]),
        ]),
        ('8.3.5', 'Organic Chemistry', [
            ('8.3.5.1', 'Alkanols', [
                'name the first ten unbranched alkanols',
                'write molecular and condensed formulae of alkanols',
                'explain polarity of alkanols',
            ]),
            ('8.3.5.2', 'Alkanals and Alkanones', [
                'state uses of alkanals and alkanones',
                'name first five straight chain alkanals and alkanones',
                'carry out tests to distinguish alkanals and alkanones',
            ]),
            ('8.3.5.3', 'Alkanoic Acids', [
                'name the first ten alkanoic acids',
                'describe physical and chemical properties',
                'investigate trends in physical properties',
            ]),
            ('8.3.5.4', 'Alkanoates', [
                'name alkanoates', 'describe the process of esterification',
                'explain the process of soap making',
            ]),
            ('8.3.5.5', 'Identification of Unknown Organic Compounds', [
                'deduce family and structural formula from information',
                'distinguish organic compounds based on tests',
            ]),
            ('8.3.5.6', 'Isomerism', [
                'name isomers using IUPAC system',
                'draw isomers of alkanes, alkenes and alkanols',
                'describe the effect of branching on physical properties',
            ]),
            ('8.3.5.7', 'Polymerisation', [
                'define monomer and polymer',
                'list examples of natural and synthetic polymers',
                'investigate differences between thermosoftening and thermosetting plastics',
            ]),
        ]),
        ('8.3.6', 'Environmental Chemistry', [
            ('8.3.6.1', 'Water', [
                'state natural sources of water', 'define water pollution',
                'describe water hardness and methods of removal',
            ]),
            ('8.3.6.2', 'Green House Gases and the Ozone Layer', [
                'define greenhouse gases', 'explain the importance of the ozone layer',
                'describe the depletion of the ozone layer by CFCs',
            ]),
            ('8.3.6.3', 'Waste Management', [
                'classify wastes based on physical state and degradability',
                'describe ways of treating and disposing wastes',
                'explain recycling of metals and plastics',
            ]),
        ]),
    ],

    # ---- M034 Clothing and Textile (MANEB 2020 §10.3) ----
    'M034': [
        ('10.3.1', 'Sewing and Knitting Equipment', [
            ('10.3.1.1', 'Sewing Machines', [
                'describe portable lock stitch and industrial machines',
                'use sewing machines based on their functions',
            ]),
            ('10.3.1.2', 'Knitting machines', [
                'describe types of knitting machines',
            ]),
        ]),
        ('10.3.2', 'Fibres and Fabrics', [
            ('10.3.2.1', 'Fibres and fabrics', [
                'differentiate characteristics of different fabrics',
                'explain factors affecting the performance of fabrics',
                'create designs on fabrics through printing and dyeing',
            ]),
            ('10.3.2.2', 'Fabric finishing techniques', [
                'describe fabric finishing techniques',
                'discuss methods of dyeing fabric',
            ]),
            ('10.3.2.3', 'Embroidery stitches', [
                'list and draw different types of embroidery stitches',
                'produce a textile article using at least five embroidery stitches',
            ]),
        ]),
        ('10.3.3', 'Design and construction of garments', [
            ('10.3.3.1', 'Design and construction of garments', [
                'state guidelines for selection of fabrics',
                'design patterns using personal body measurements',
                'construct a garment of choice',
            ]),
        ]),
        ('10.3.4', 'Principles and elements of design', [
            ('10.3.4.1', 'Principles and elements of design', [
                'define design in garment construction', 'list sources of design',
            ]),
            ('10.3.4.2', 'Interior design', [
                'define interior design', 'discuss room decoration accessories',
            ]),
            ('10.3.4.3', 'Fashion', [
                'define fashion in clothing and textiles',
                'describe factors which affect fashion selection',
                'discuss characteristics of fashion',
            ]),
        ]),
        ('10.3.5', 'Maintenance of Clothing and Textile products', [
            ('10.3.5.1', 'Maintenance', [
                'list laundry materials and methods of mending',
                'describe guidelines for stain removal',
            ]),
            ('10.3.5.2', 'Laundry', [
                'describe stages in laundry processes',
                'explain methods of washing fabrics',
                'analyse properties of cotton, nylon, wool and polyester',
            ]),
        ]),
        ('10.3.6', 'Consumerism and Entrepreneurship', [
            ('10.3.6.1', 'Consumerism', [
                'state problems affecting the consumer',
                'explain responsibilities and rights of the consumer',
            ]),
            ('10.3.6.2', 'Entrepreneurship', [
                'define entrepreneurship in clothing and textiles',
                'interpret textile product labels',
                'discuss steps in developing a small scale business',
            ]),
            ('10.3.6.3', 'Market research', [
                'define market research', 'describe the importance of marketing',
                'plan a small scale clothing and textile business',
            ]),
            ('10.3.6.4', 'Business plan', [
                'list financing institutions for small businesses',
                'describe components of a business plan',
            ]),
        ]),
    ],

    # ---- M039 Computer Studies (MANEB 2020 §11.3) ----
    'M039': [
        ('11.3.1', 'Application Software', [
            ('11.3.1.1', 'Spreadsheets', [
                'define spreadsheets and worksheets',
                'differentiate relative, mixed and absolute cell references',
                'create a worksheet and workbook',
                'use shortcuts, formulae and built-in functions',
                'create charts and graphs',
            ]),
            ('11.3.1.2', 'Desktop Publishing', [
                'state examples of desktop publishing software',
                'create and edit a publication',
                'print a publication',
            ]),
            ('11.3.1.3', 'Databases', [
                'state features and objects of databases',
                'distinguish among different database models',
                'design and create tables, queries, forms and reports',
            ]),
        ]),
        ('11.3.2', 'Personal Computer Management and Maintenance', [
            ('11.3.2.1', 'Software Installation', [
                'describe installation of operating systems and drivers',
                'describe the procedure for upgrading software',
            ]),
            ('11.3.2.2', 'Troubleshooting', [
                'state hardware problems, sources and solutions',
                'state software problems, sources and solutions',
            ]),
        ]),
        ('11.3.3', 'Communication Networks', [
            ('11.3.3.1', 'Introduction to Communication Technologies', [
                'define communication and telecommunication network',
                'list network devices',
                'explain how data signals are transmitted',
            ]),
            ('11.3.3.2', 'Introduction to computer networks', [
                'describe types of computer networks and topologies',
                'describe the OSI and TCP/IP reference models',
                'compare classful and classless IP addressing',
            ]),
            ('11.3.3.3', 'Network Applications', [
                'list examples of distributed applications and web browsers',
                'state advantages and disadvantages of social networks',
                'describe how to use search engines and email',
            ]),
        ]),
        ('11.3.4', 'Programming Techniques and Logical Methods', [
            ('11.3.4.1', 'Programming fundamentals', [
                'define programme, compiler, translator and assembler',
                'state examples of programming languages',
                'describe the process of developing a programme',
            ]),
        ]),
    ],

    # ---- M015 Creative Arts (MANEB 2020 §12.3) ----
    'M015': [
        ('12.3.1', 'Creating, interpreting and presenting artworks', [
            ('12.3.1.1', 'Design and lettering', [
                'state different types and styles of writings found in the locality',
                'design posters, billboards and sign writings in colour',
                'draw human and animal figures in different positions',
            ]),
            ('12.3.1.2', 'Fabric printing', [
                'state factors to consider when pricing finished fabrics',
                'design patterns on lino, rubber and soft wood',
            ]),
        ]),
        ('12.3.2', 'Entrepreneurship in creative arts', [
            ('12.3.2.1', 'Tie and dye and batik', [
                'define tie and dye and batik',
                'describe the process of making tie and dye',
                'explain factors to consider when pricing tie and batik',
            ]),
            ('12.3.2.2', 'Career opportunities in creative arts', [
                'describe career opportunities in the art industry',
                'design advertisements for artworks',
            ]),
        ]),
        ('12.3.3', 'Expressing and communicating', [
            ('12.3.3.1', 'Figures and portrait drawing', [
                'explain the principles of proportion in figures and portraits',
                'draw complete human figures and portraits',
            ]),
            ('12.3.3.2', 'Animal figures', [
                'explain principles of proportion in animal figures',
                'draw animal figures',
            ]),
            ('12.3.3.3', 'Still life and nature', [
                'describe various forms of still life and nature',
                'draw and paint still life and nature artworks',
            ]),
            ('12.3.3.4', 'Design and lettering', [
                'write a stanza in freehand pen lettering',
                'design a book cover and logos',
                'produce designs using a computer',
            ]),
        ]),
        ('12.3.4', 'Environmental friendly art production practices', [
            ('12.3.4.1', 'Conserving the environment', [
                'mention alternative resources for producing artworks',
                'design a poster depicting dangers of environmental degradation',
            ]),
            ('12.3.4.2', 'Paper carving', [
                'describe the process for making paper pulp',
                'design various artworks using paper pulp blocks',
            ]),
        ]),
        ('12.3.5', 'Entrepreneurship in creative arts (continued)', [
            ('12.3.5.1', 'Clay modelling and pottery', [
                'describe the procedure for processing clay',
                'explain moulding techniques for clay artworks',
                'distinguish methods of firing clay artwork',
            ]),
            ('12.3.5.2', 'Weaving and plaiting', [
                'distinguish between weaving and plaiting',
                'explain types of weaving',
                'explain factors to consider when pricing woven items',
            ]),
            ('12.3.5.3', 'Craftwork in wood and stone', [
                'explain qualities of wood suitable for carving',
                'describe qualities of stone suitable for carving',
                'design different objects for wood carving',
            ]),
        ]),
        ('12.3.6', 'Expressing and communicating (continued)', [
            ('12.3.6.1', 'Perspective drawing', [
                'mention objects that depict perspective',
                'explain the principles of perspective drawing',
                'draw and paint objects that depict perspective',
            ]),
            ('12.3.6.2', 'Landscape drawing', [
                'draw and paint various landscapes',
                'design a landscape using computers',
            ]),
            ('12.3.6.3', 'Imaginative abstract and realistic compositions', [
                'define imaginative realistic compositions',
                'distinguish between realistic and abstract compositions',
                'draw and paint cartoon compositions',
            ]),
        ]),
    ],

    # ---- M052 English (MANEB 2020 §13) ----
    'M052': [
        ('13.5.1', 'Grammar and Composition', [
            ('13.5.1.1', 'Grammar', [
                'demonstrate knowledge of English grammar, vocabulary and usage',
                'use prepositional structures and registers',
                'use verb tenses and conditional sentences',
                'use phrasal verbs and parts of speech correctly',
            ]),
            ('13.5.1.2', 'Composition', [
                'write a business or formal letter',
                'write a speech', 'write a report', 'write a short story',
                'observe the required number of words (350-500)',
            ]),
        ]),
        ('13.5.2', 'Summary and Comprehension', [
            ('13.5.2.1', 'Note-making', [
                'provide a suitable title in capital letters',
                'give four main points numbered and underlined',
                'supply at least 16 supporting points',
            ]),
            ('13.5.2.2', 'Comprehension', [
                'make inferences from material in the passage',
                'extract information from the passage',
                'summarise points in the candidate\'s own words',
            ]),
        ]),
        ('13.5.3', 'Literature in English', [
            ('13.5.3.1', 'Poetry and Short Story (contextual)', [
                'identify literary terms and devices',
                'describe characters using adjectives with evidence',
                'explain plot, tone, mood and theme',
            ]),
            ('13.5.3.2', 'Essay questions', [
                'analyse character, theme, plot and literary devices',
                'support arguments with evidence from the prescribed books',
            ]),
            ('13.5.3.3', 'Prescribed books', [
                'analyse The Pearl (novel)',
                'analyse Macbeth (play)',
            ]),
        ]),
    ],

    # ---- M061 French (MANEB 2020 §14) ----
    'M061': [
        ('14.3.1', 'Paper I: Oral/Aural examinations', [
            ('14.3.1.1', 'Compréhension orale', [
                'comprendre ce qui est dit ou lu',
                'répondre aux questions en français',
            ]),
            ('14.3.1.2', 'Dictée', [
                'écrire correctement un texte lu',
                'respecter l\'orthographe et la ponctuation',
            ]),
            ('14.3.1.3', 'Épreuves orales', [
                'lire un texte avec bonne prononciation et intonation',
                'décrire une série d\'images',
                'tenir une conversation générale',
            ]),
        ]),
        ('14.3.2', 'Paper II: Composition and Grammar', [
            ('14.3.2.1', 'Composition', [
                'écrire une conversation, une lettre ou une composition',
                'respecter le nombre de mots requis (120-150)',
            ]),
            ('14.3.2.2', 'Grammaire', [
                'maîtriser la négation, les prépositions et les conjonctions',
                'utiliser correctement les temps de verbes',
                'maîtriser le discours direct et indirect',
            ]),
        ]),
        ('14.3.3', 'Paper III: Comprehension and Summary', [
            ('14.3.3.1', 'Compréhension du texte', [
                'répondre à dix questions en français',
                's\'exprimer dans un contexte approprié',
            ]),
            ('14.3.3.2', 'Résumé du texte', [
                'résumer le texte en 70 à 100 mots',
                'utiliser les connecteurs logiques',
            ]),
        ]),
    ],

    # ---- M073 Geography (MANEB 2020 §15.3) ----
    'M073': [
        ('15.3.1', 'Map reading and interpretation', [
            ('15.3.1.1', 'Land uses', [
                'identify land uses on topographical maps',
                'interpret map symbols in relation to land uses',
            ]),
            ('15.3.1.2', 'Land forms', [
                'define landforms',
                'identify landforms on topographical maps',
                'draw cross-sections of relief features',
            ]),
            ('15.3.1.3', 'Map work', [
                'measure distance between points on a map',
                'calculate area and gradient',
                'draw cross sections of river profiles',
                'reduce and enlarge maps',
            ]),
            ('15.3.1.4', 'Statistical methods', [
                'identify ways of collecting geographical data',
                'design data collection tools',
            ]),
        ]),
        ('15.3.2', 'Understanding the earth', [
            ('15.3.2.1', 'Riverine landforms', [
                'identify riverine landforms',
                'explain the formation and importance of riverine landforms',
            ]),
            ('15.3.2.2', 'Coastal landforms', [
                'describe coastal landforms',
                'explain the formation and importance of coastal landforms',
            ]),
            ('15.3.2.3', 'Theory of continental drift', [
                'explain the continental drift theory',
                'examine evidence supporting the theory',
            ]),
            ('15.3.2.4', 'Theory of plate tectonics', [
                'identify types of crustal plates',
                'explain the theory of plate tectonics',
                'relate plate tectonics and continental drift theory',
            ]),
            ('15.3.2.5', 'Mountain building processes', [
                'define folding and faulting',
                'describe features formed from faulting and folding',
                'relate mountain building processes to plate tectonics',
            ]),
            ('15.3.2.6', 'Volcanism', [
                'describe the formation of a volcano',
                'explain intrusive and extrusive volcanic features',
                'analyse effects of volcanism',
            ]),
            ('15.3.2.7', 'Earthquakes', [
                'explain causes of earthquakes',
                'describe the process of measuring and detecting earthquakes',
                'analyse effects of earthquakes',
            ]),
            ('15.3.2.8', 'Rocks', [
                'describe main types of rocks',
                'explain the formation of different types of rocks',
                'draw the rock cycle',
            ]),
            ('15.3.2.9', 'Relief features of ocean basins', [
                'identify relief features of the ocean basin',
                'draw the relief features of the oceanic basin',
            ]),
            ('15.3.2.10', 'Ocean currents', [
                'identify types of ocean currents',
                'locate major ocean currents of the world',
                'examine effects of ocean currents',
            ]),
            ('15.3.2.11', 'World fishing', [
                'identify main species caught in major fishing grounds',
                'explain factors influencing the fishing industry',
            ]),
            ('15.3.2.12', 'World pressure belts', [
                'define air pressure',
                'locate major air pressure belts of the world',
            ]),
            ('15.3.2.13', 'Prevailing winds', [
                'explain how pressure belts influence prevailing winds',
                'plot isobars on a pressure map',
            ]),
            ('15.3.2.14', 'Local winds', [
                'distinguish prevailing winds from local winds',
                'explain occurrence of land and sea breeze',
            ]),
            ('15.3.2.15', 'Air masses', [
                'explain types of air masses',
                'classify air masses',
            ]),
            ('15.3.2.16', 'Fronts', [
                'describe different types of fronts',
                'explain the formation of fronts',
            ]),
            ('15.3.2.17', 'Cyclones and anticyclones', [
                'identify different types of cyclones',
                'compare weather patterns of tropical and temperate cyclones',
            ]),
            ('15.3.2.18', 'Clouds', [
                'identify types of clouds',
                'explain how clouds are formed',
            ]),
            ('15.3.2.19', 'Precipitation and Rainfall', [
                'explain the formation of different types of rainfall',
                'interpret rainfall data',
            ]),
            ('15.3.2.20', 'Climatic regions and vegetation biomes', [
                'identify climatic regions',
                'explain influence of climate on human activities',
            ]),
        ]),
        ('15.3.3', 'Environment and natural resources management', [
            ('15.3.3.1', 'Environmental issues', [
                'define environmental issues and pollution',
                'explain causes and effects of different types of pollution',
            ]),
            ('15.3.3.2', 'Desertification', [
                'explain causes of desertification',
                'examine effects of desertification',
            ]),
            ('15.3.3.3', 'Climate change', [
                'explain causes and effects of climate change',
                'explain climate change mitigation and adaptation measures',
            ]),
            ('15.3.3.4', 'Wetlands in Malawi', [
                'locate wetlands on the map of Malawi',
                'explain strategies of managing wetlands',
            ]),
            ('15.3.3.5', 'Wildlife in Malawi', [
                'locate wildlife reserves on the map of Malawi',
            ]),
            ('15.3.3.6', 'Waste management', [
                'explain different types of waste',
                'explain ways of managing waste',
            ]),
            ('15.3.3.7', 'Minerals', [
                'describe major mining methods',
                'explain uses of coal and gold',
            ]),
            ('15.3.3.8', 'Uranium', [
                'locate places where uranium is found in Malawi',
                'describe the process of mining and processing uranium',
            ]),
            ('15.3.3.9', 'Petroleum', [
                'locate areas with petroleum deposits',
                'describe formation, extraction and refining of petroleum',
            ]),
            ('15.3.3.10', 'Energy', [
                'describe types of energy',
                'explain environmental impact of each form of energy',
            ]),
        ]),
        ('15.3.4', 'Spatial organisation', [
            ('15.3.4.1', 'Population distribution', [
                'identify areas of low, medium and high population density',
                'account for world population distribution',
            ]),
            ('15.3.4.2', 'Population growth', [
                'explain causes and effects of population growth',
                'describe strategies for controlling population growth',
            ]),
            ('15.3.4.3', 'Population structure', [
                'draw age-sex pyramids',
                'compare population structures for developing and developed countries',
            ]),
            ('15.3.4.4', 'Demographic transition model', [
                'analyse the demographic transition model',
            ]),
            ('15.3.4.5', 'Settlements', [
                'identify types of settlements',
                'examine different settlement patterns',
            ]),
            ('15.3.4.6', 'Urbanisation', [
                'explain the concentric zonal model',
                'relate urbanisation to Lilongwe city',
            ]),
            ('15.3.4.7', 'World distribution of farming activities', [
                'explain factors that influence agriculture',
                'differentiate intensive and extensive farming',
            ]),
            ('15.3.4.8', 'Intensive rice farming in South East Asia', [
                'explain conditions favouring rice farming in S.E. Asia',
            ]),
            ('15.3.4.9', 'Intensive animal farming in Denmark', [
                'explain factors favouring dairy farming in Denmark',
                'explain the role of cooperatives',
            ]),
            ('15.3.4.10', 'Irrigation farming', [
                'describe modern methods of irrigation',
                'explain challenges associated with irrigation farming',
            ]),
            ('15.3.4.11', 'Irrigation in Israel', [
                'explain factors that influence irrigation farming in Israel',
                'compare crops grown under irrigation in Malawi and Israel',
            ]),
            ('15.3.4.12', 'Plantation farming', [
                'identify areas where plantation farming is practiced',
                'assess the value of plantation farming',
            ]),
            ('15.3.4.13', 'Tea plantation in Malawi', [
                'locate tea growing areas on the map of Malawi',
                'describe stages in the processing of tea',
            ]),
            ('15.3.4.14', 'Industrialisation', [
                'explain advantages and disadvantages of industrialisation',
            ]),
            ('15.3.4.15', 'Industries', [
                'explain types of industries',
                'locate the major industrialised areas of the world',
            ]),
            ('15.3.4.16', 'Motor vehicle industry in Japan', [
                'explain factors for the growth of the motor vehicle industry in Japan',
            ]),
            ('15.3.4.17', 'Tourism in Africa', [
                'locate major tourist centres in Africa',
                'assess the impact of tourism in Africa',
            ]),
        ]),
        ('15.3.5', 'Interdependence between Malawi and the world', [
            ('15.3.5.1', 'Regional and international trade blocks', [
                'identify regional and world trade blocks',
                'examine roles of customs in international trade',
            ]),
            ('15.3.5.2', 'World transport routes', [
                'identify major sea, air and railway routes',
                'describe challenges faced by land locked countries',
            ]),
        ]),
    ],

    # ---- M081 History (MANEB 2020 §16.3) ----
    'M081': [
        ('16.3.1', 'Interrelationships Among the Individual, Family and Society', [
            ('16.3.1.1', 'The Yao and the Lomwe', [
                'trace migratory routes of the Yao and Lomwe',
                'give reasons for their migration',
            ]),
            ('16.3.1.2', 'The Jere and Maseko Ngoni', [
                'trace their migratory routes',
                'describe their socio-political organisation',
            ]),
            ('16.3.1.3', 'The Ndebele', [
                'trace their migratory routes',
                'describe their socio-political organisation',
            ]),
        ]),
        ('16.3.2', 'Economic and Social Issues in History', [
            ('16.3.2.1', 'Growth of trade in Pre-colonial East and Central Africa', [
                'explain the decline of Portuguese influence',
                'explain causes and results of the Arab-Portuguese conflict',
            ]),
            ('16.3.2.2', 'Ivory and Slave Trade', [
                'describe the organisation of Ivory and Slave trade',
                'explain the impact on indigenous people',
            ]),
        ]),
        ('16.3.3', 'Interdependence Between Malawi and the World', [
            ('16.3.3.1', 'Islam', [
                'locate areas where Islam spread',
                'give reasons for the rapid spread of Islam among the Yao',
            ]),
            ('16.3.3.2', 'Christianity', [
                'give objectives of Dr David Livingstone\'s work',
                'describe early Christian churches in Malawi',
            ]),
        ]),
        ('16.3.4', 'Patriotism and Nationalism', [
            ('16.3.4.1', 'Southern Rhodesia', [
                'describe the role of the British South African Company',
                'assess the impact of administrative policies on local population',
            ]),
            ('16.3.4.2', 'Northern Rhodesia', [
                'describe the role of the British South African Company',
                'describe the roles of Alfred Sharpe and Sir Harry Johnston',
            ]),
            ('16.3.4.3', 'Nyasaland', [
                'explain factors that led to British, German and Portuguese interests',
                'describe the process of British occupation of Nyasaland',
                'analyse the significance of the Chilembwe uprising',
            ]),
        ]),
        ('16.3.5', 'Leadership Styles in History', [
            ('16.3.5.1', 'Economic developments in central Africa', [
                'describe the development of the mining industry',
                'assess the impact of labour migration on Nyasaland',
            ]),
            ('16.3.5.2', 'Political developments in central Africa', [
                'state reasons for African opposition to the Central African Federation',
                'explain successes and failures of the Federation',
            ]),
            ('16.3.5.3', 'The role of African independent churches in nationalism', [
                'explain factors that led to the formation of African independent churches',
                'describe their role towards nationalism',
            ]),
        ]),
        ('16.3.6', 'Causes and results of the First World War', [
            ('16.3.6.1', 'Causes and results of the First World War', [
                'explain causes of the First World War',
                'assess the impact of the First World War',
            ]),
        ]),
        ('16.3.7', 'Developments in the inter-war period', [
            ('16.3.7.1', 'The Paris Peace Conference and Versailles Treaty', [
                'outline the terms of the Versailles Treaty',
                'assess strengths and weaknesses of the Treaty',
            ]),
            ('16.3.7.2', 'The League of Nations', [
                'describe the origins of the League of Nations',
                'assess strengths and weaknesses of the League',
            ]),
            ('16.3.7.3', 'Economic problems in Europe', [
                'describe the economic conditions in Europe after WWI',
            ]),
            ('16.3.7.4', 'Economic situation in Asia (Japan)', [
                'explain the impact of WWI on the Japanese economy',
            ]),
            ('16.3.7.5', 'The Great Depression', [
                'explain causes of the Great Depression',
                'explain how the New Deal attempted to solve the problems',
            ]),
            ('16.3.7.6', 'The Communist Revolution in Russia', [
                'explain causes of the 1905 and 1917 revolutions',
                'outline Lenin\'s achievements and failures',
            ]),
        ]),
        ('16.3.8', 'Autocratic governments in Europe (Germany)', [
            ('16.3.8.1', 'Development of autocratic governments in Europe', [
                'describe the rise of Adolf Hitler to power',
                'assess Hitler\'s domestic and foreign policies',
            ]),
        ]),
        ('16.3.9', 'Patriotism and Nationalism (continued)', [
            ('16.3.9.1', 'The Second World War', [
                'explain causes of the Second World War',
                'describe highlights of the Second World War',
            ]),
            ('16.3.9.2', 'Formation of the United Nations Organisation', [
                'describe origins of the UNO',
                'compare the League of Nations and the UNO',
            ]),
            ('16.3.9.3', 'Post-war alliances', [
                'describe post-war alliances (NATO, Warsaw Pact, COMECON)',
                'explain the impact of the post-war alliances',
            ]),
            ('16.3.9.4', 'The Cold War', [
                'explain causes of the Cold War',
                'explain the impact of Cold War on Africa',
            ]),
            ('16.3.9.5', 'Decolonisation: Asia (India)', [
                'trace the main stages leading to the independence of India',
                'explain the causes and impact of Hindu-Muslim rivalry',
            ]),
            ('16.3.9.6', 'Decolonisation: Africa (Kenya)', [
                'explain factors that led to the rise of nationalism in Kenya',
                'describe the formation of KANU and KADU',
            ]),
        ]),
        ('16.3.10', 'Post-colonial Africa up to 2000', [
            ('16.3.10.1', 'Post-colonial Africa up to 2000', [
                'describe the expectations of Africans at independence',
                'explain socio-economic and political achievements and challenges',
            ]),
        ]),
    ],

    # ---- M082 Home Economics (MANEB 2020 §17.3) ----
    'M082': [
        ('17.3.1', 'Kitchen Equipment', [
            ('17.3.1.1', 'Choice, care and maintenance of large kitchen equipment', [
                'list large kitchen equipment',
                'discuss guidelines for choosing large kitchen equipment',
                'discuss ways of caring for large kitchen equipment',
            ]),
            ('17.3.1.2', 'Choice, care and maintenance of electrical kitchen equipment', [
                'list electrical kitchen appliances',
                'describe ways of caring for appliances',
            ]),
        ]),
        ('17.3.2', 'Food and Nutrition', [
            ('17.3.2.1', 'Nutritive value of food', [
                'analyse main foods used in food preparation',
                'discuss nutritive value of main foods',
            ]),
            ('17.3.2.2', 'Food technology', [
                'list food processing technologies in the home',
            ]),
            ('17.3.2.3', 'Food processing', [
                'define food processing',
                'describe common ways of processing food in the home',
            ]),
            ('17.3.2.4', 'Flour and flour mixtures', [
                'define raising agents', 'list examples of raising agents',
                'describe methods of incorporating raising agents',
            ]),
            ('17.3.2.5', 'Food preservation', [
                'define food preservation',
                'state different ways of preserving food',
                'conduct an experiment on effects of heat, acids and freezing on food nutrients',
            ]),
            ('17.3.2.6', 'Principles of nutrition', [
                'define nutrition and nutrient',
                'discuss chemical composition and functions of nutrients',
            ]),
            ('17.3.2.7', 'Meal planning', [
                'define meal planning',
                'discuss guidelines for meal planning',
                'plan meals for different occasions',
            ]),
            ('17.3.2.8', 'HIV and AIDS and Nutrition', [
                'discuss progression of HIV to AIDS in relation to nutrition',
                'analyse nutritional care and support for PLWHA',
            ]),
            ('17.3.2.9', 'Convenience foods', [
                'define convenience food',
                'analyse the importance of convenience foods',
            ]),
            ('17.3.2.10', 'Left over foods (Rechauffe cookery)', [
                'define left over foods',
                'discuss guidelines to be followed when reheating left over foods',
            ]),
            ('17.3.2.11', 'Packed meals', [
                'define packed meals', 'plan meals for packing',
            ]),
            ('17.3.2.12', 'Entertaining', [
                'discuss types and etiquette of entertainment',
                'prepare meals for entertainment',
            ]),
            ('17.3.2.13', 'Food additives', [
                'define food additives',
                'list different types of food additives',
                'conduct an experiment on effects of food additives',
            ]),
            ('17.3.2.14', 'Food industry in Malawi', [
                'describe types of food industries in Malawi',
                'analyse the role of the Malawi Bureau of Standards',
            ]),
            ('17.3.2.15', 'Nutritional related disorders', [
                'list common nutrition related disorders',
                'discuss causes and preventive measures',
            ]),
            ('17.3.2.16', 'Nutritional status of Malawi', [
                'define nutritional status',
                'explain factors influencing poor nutritional status',
            ]),
            ('17.3.2.17', 'Food security', [
                'define food security and population growth',
                'analyse impact of population growth on food security',
            ]),
            ('17.3.2.18', 'Household food demand and supply', [
                'analyse factors affecting food demand and supply',
            ]),
            ('17.3.2.19', 'Meal planning for manual and sedentary workers', [
                'discuss nutritional requirements for manual and sedentary workers',
                'plan meals for adults and the elderly',
            ]),
            ('17.3.2.20', 'Management of HIV and AIDS related illnesses', [
                'list micronutrients important in HIV and AIDS management',
                'analyse management of opportunistic infections',
            ]),
        ]),
        ('17.3.3', 'Human Growth and Development', [
            ('17.3.3.1', 'Human growth and development during adolescent', [
                'define adolescence and good grooming',
                'discuss reproductive health issues during adolescence',
            ]),
            ('17.3.3.2', 'Human growth and development from adulthood to old age', [
                'list reproductive health services for adults and the elderly',
                'discuss challenges in adulthood and old age',
            ]),
        ]),
        ('17.3.4', 'Housing and Environment', [
            ('17.3.4.1', 'Housing, population, environment and sustainable development', [
                'define population, environment and sustainable development',
                'discuss risk management strategies in the home',
            ]),
            ('17.3.4.2', 'Care of the dining room', [
                'discuss daily and weekly cleaning of the dining room',
                'launder table linen',
            ]),
            ('17.3.4.3', 'Housing', [
                'list housing institutions and programmes in Malawi',
                'discuss roles of housing institutions',
            ]),
            ('17.3.4.4', 'Care for the sitting room and toilet', [
                'list types of toilets',
                'discuss guidelines for cleaning the sitting room and toilets',
            ]),
        ]),
        ('17.3.5', 'Family Resource Management', [
            ('17.3.5.1', 'Decision Making', [
                'define decision making',
                'discuss factors that influence decision making in the home',
            ]),
            ('17.3.5.2', 'Entrepreneurship', [
                'define entrepreneurship in home economics',
                'draft a small scale business plan',
            ]),
            ('17.3.5.3', 'Taxes and Entrepreneurship', [
                'list various forms of taxes that affect business enterprises',
            ]),
            ('17.3.5.4', 'Risk management in business enterprises', [
                'define risk management', 'list different investment opportunities',
            ]),
            ('17.3.5.5', 'Consumerism', [
                'define consumerism',
                'discuss the right and responsibilities of the consumer',
            ]),
            ('17.3.5.6', 'Financial management', [
                'define savings and budget',
                'plan a monthly family budget',
            ]),
            ('17.3.5.7', 'Insurance', [
                'list various types of insurance', 'analyse different types of insurance',
            ]),
            ('17.3.5.8', 'Human resource management in the home', [
                'list types of human resources and labour saving devices',
                'discuss management of human resource in the home',
            ]),
            ('17.3.5.9', 'Time management', [
                'describe time management',
                'discuss ways of managing time',
            ]),
        ]),
    ],

    # ---- M131 Mathematics (MANEB 2020 §18.3) ----
    'M131': [
        ('18.3.1', 'Number and Numeration', [
            ('18.3.1.1', 'Quadratic Equations', [
                'factorise quadratic expressions where the coefficient of x² is not 1',
                'solve quadratic equations by completing the square or using the formula',
                'solve real life problems using quadratic equation concepts',
            ]),
            ('18.3.1.2', 'Irrational Numbers', [
                'simplify irrational numbers',
                'rationalise surd denominators with a single term',
                'rationalise surd denominators using conjugate surds',
            ]),
            ('18.3.1.3', 'Algebraic Fractions', [
                'add, subtract, multiply and divide algebraic fractions',
            ]),
            ('18.3.1.4', 'Subject of the Formula', [
                'change the subject of formulae or equations with powers up to 3',
            ]),
            ('18.3.1.5', 'Exponential and Logarithmic Equations', [
                'solve equations involving exponents',
                'solve equations involving logarithms',
            ]),
            ('18.3.1.6', 'Matrices', [
                'add or subtract 2x2 matrices',
                'multiply matrix by scalar and two matrices',
            ]),
            ('18.3.1.7', 'Simultaneous Equations', [
                'solve a linear and a quadratic equation by substitution',
                'solve real life problems involving simultaneous equations',
            ]),
            ('18.3.1.8', 'Progressions', [
                'calculate nth term, common difference and sum of AP or GP',
                'apply AP concepts in solving real life problems',
            ]),
            ('18.3.1.9', 'Polynomials', [
                'find the remainder of polynomials using long division',
                'factorise and solve cubic equations',
                'find coefficients in identical polynomials',
            ]),
        ]),
        ('18.3.2', 'Structure', [
            ('18.3.2.1', 'Sets', [
                'list elements of compliments, unions and intersections',
                'draw Venn diagrams',
                'solve real life problems using sets',
            ]),
            ('18.3.2.2', 'Transformations', [
                'draw rotations and translations of plane figures',
                'calculate coordinates of image and object points',
                'draw enlargements of plane figures',
            ]),
            ('18.3.2.3', 'Vectors', [
                'carry out basic operations on vectors',
                'calculate magnitude or mid-point of a vector',
                'show that points are collinear using vector method',
                'solve problems using triangular or parallelogram law',
            ]),
        ]),
        ('18.3.3', 'Space, Shape and Measurement', [
            ('18.3.3.1', 'Circle Geometry (Chord Properties)', [
                'calculate the length of a chord given radius and distance',
                'calculate distance from centre given chord and radius',
            ]),
            ('18.3.3.2', 'Circle Geometry (Angle Properties)', [
                'write formal proofs of angle properties theorems',
                'apply theorems to calculate angles',
                'show that points are concyclic',
            ]),
            ('18.3.3.3', 'Tangents to Circles', [
                'write formal proofs of the theorems of tangents',
                'construct tangents to circles',
            ]),
            ('18.3.3.4', 'Trigonometry', [
                'calculate angles and sides of right-angled triangles',
                'solve real life problems using trigonometric ratios',
                'calculate side, angle and area using sine and cosine rules',
            ]),
            ('18.3.3.5', 'Similarity', [
                'calculate ratios of areas and volumes of similar shapes',
                'calculate scale factor given areas or volumes',
            ]),
            ('18.3.3.6', 'Mensuration', [
                'calculate surface areas and volumes of 3-D shapes',
                'calculate surface areas and volumes of composite shapes',
                'calculate angles between lines and planes',
            ]),
        ]),
        ('18.3.4', 'Patterns, Relations, Functions and Change', [
            ('18.3.4.1', 'Mappings and Functions', [
                'draw arrow diagrams from given domain or range',
                'calculate the range given domain or the domain given range',
            ]),
            ('18.3.4.2', 'Coordinate Geometry', [
                'calculate distance between two points',
                'find the equation of a line in the form y = mx + c',
                'calculate the mid-point of a line segment',
            ]),
            ('18.3.4.3', 'Variations', [
                'solve problems on joint variations',
                'solve partial variation problems',
            ]),
            ('18.3.4.4', 'Inequalities', [
                'sketch graphs to show regions represented by inequalities',
            ]),
            ('18.3.4.5', 'Travel Graphs', [
                'draw velocity-time graphs',
                'calculate speed, time and acceleration using velocity-time graphs',
                'calculate distance as area under a velocity-time graph',
            ]),
            ('18.3.4.6', 'Linear Programming', [
                'solve linear programming problems by sketching graphs',
            ]),
            ('18.3.4.7', 'Graphs of Functions', [
                'solve linear and quadratic or cubic equations graphically',
                'formulate a quadratic equation given a graph',
                'find line of symmetry, maximum or minimum value',
            ]),
        ]),
        ('18.3.5', 'Statistics', [
            ('18.3.5.1', 'Statistics', [
                'calculate median, variance and standard deviation of ungrouped data',
                'calculate mean and mode of grouped data',
                'present statistical data in tables and diagrams',
            ]),
            ('18.3.5.2', 'Probability', [
                'calculate probability of two or more events',
                'use probability space tables and tree diagrams',
            ]),
        ]),
    ],

    # ---- M133 Metalwork (MANEB 2020 §19.3) ----
    'M133': [
        ('19.3.1', 'Production Technology', [
            ('19.3.1.1', 'Safety', [
                'discuss general safety working conditions in a workshop',
                'explain safe use of machine tools',
                'describe care and maintenance of machine tools',
            ]),
            ('19.3.1.2', 'Materials', [
                'describe working characteristics of materials',
            ]),
            ('19.3.1.3', 'Hand Tools and Processes', [
                'define terms related to hand processes',
                'discuss types of limits and fits',
                'sketch tool profiles',
            ]),
            ('19.3.1.4', 'Machine Tools and Processes', [
                'state uses of centre lathe accessories',
                'describe operations on a lathe machine',
                'explain shaping processes',
            ]),
            ('19.3.1.5', 'Machine Forging', [
                'state advantages and disadvantages of press and drop forging',
                'explain machine forging processes',
            ]),
            ('19.3.1.6', 'Theory of Metal Cutting', [
                'state functions of coolants, cutting solutions and lubricants',
                'describe cutting angles',
                'calculate cutting speeds',
            ]),
            ('19.3.1.7', 'Sheet Metal', [
                'name tools used in sheet metalwork',
                'describe safety hazards related to sheet metal working',
                'produce artifacts through the design process',
            ]),
            ('19.3.1.8', 'Arc Welding', [
                'state welding consumables',
                'describe parts and accessories of a welding machine',
                'prepare and weld different types of joints',
            ]),
            ('19.3.1.9', 'Oxy-fuel Gas Welding', [
                'discuss safe welding and handling behaviour',
                'describe parts of welding equipment',
                'join metals using oxy-fuel gas welding',
            ]),
            ('19.3.1.10', 'Metal Finishing', [
                'describe different types of finishes',
                'explain methods of finishing metal',
            ]),
        ]),
        ('19.3.2', 'Design Process and Realisation', [
            ('19.3.2.1', 'The Design Process', [
                'develop an idea for designing',
                'conduct an investigation',
                'generate and sketch possible ideas',
                'mobilise resources, produce and evaluate products',
            ]),
        ]),
        ('19.3.3', 'Entrepreneurship', [
            ('19.3.3.1', 'Marketing', [
                'define marketing terms in relation to metalwork',
                'describe marketing processes',
            ]),
            ('19.3.3.2', 'Resource Management', [
                'give examples of assets',
                'discuss financial resource management',
            ]),
            ('19.3.3.3', 'Costing and Pricing', [
                'define direct and indirect costs',
                'explain factors that affect cost and price of metal products',
            ]),
        ]),
    ],

    # ---- M164 Physics (MANEB 2020 §20.3) ----
    'M164': [
        ('20.3.1', 'Scientific Investigation and Skills', [
            ('20.3.1.1', 'Measurement', [
                'read scales of various measuring instruments',
                'express quantities in standard notation and SI units',
                'convert one unit to another',
            ]),
            ('20.3.1.2', 'Scientific Investigation', [
                'identify types and sources of errors',
                'design a scientific investigation',
            ]),
        ]),
        ('20.3.2', 'Properties of Matter', [
            ('20.3.2.1', 'Kinetic Theory of Matter', [
                'state the meaning of absolute temperature',
                'explain the cause of gas pressure',
                'describe the kinetic theory of solids, liquids and gases',
            ]),
            ('20.3.2.2', 'Thermometry', [
                'identify various types of thermometers',
                'differentiate types of temperature scales',
                'convert temperature from one scale to another',
            ]),
            ('20.3.2.3', 'Thermal Expansion', [
                'define temperature', 'differentiate heat from temperature',
                'describe thermal expansion in solids, liquids and gases',
                'explain the unusual expansion of water',
            ]),
            ('20.3.2.4', 'Pressure', [
                'define pressure', 'state SI units of pressure',
                "explain Archimedes' principle",
                'derive the formula p = ρgh',
            ]),
            ('20.3.2.5', 'Gas Laws', [
                'state gas laws', 'explain gas laws using kinetic theory',
                'describe how a manometer works',
            ]),
        ]),
        ('20.3.3', 'Mechanics', [
            ('20.3.3.1', 'Scalar and Vector Quantities', [
                'define scalar and vector quantities',
                'add and subtract vectors using parallelogram and triangle rules',
                'resolve vectors into horizontal and vertical components',
            ]),
            ('20.3.3.2', 'Linear Motion', [
                'describe distance, displacement, speed, velocity and acceleration',
                'plot and interpret graphs of linear motion',
            ]),
            ('20.3.3.3', 'Work and Energy', [
                'state the energy-work theorem',
                'explain the conservation of mechanical energy',
                'calculate work done by a force',
            ]),
            ('20.3.3.4', 'Machines', [
                'explain mechanical advantage, velocity ratio and efficiency',
                'calculate these quantities for a machine',
            ]),
            ('20.3.3.5', "Newton's laws of motion", [
                "state Newton's three laws of motion",
                'derive the equation F = ma',
                'solve problems involving Newton\'s laws',
            ]),
            ('20.3.3.6', 'Frictional force', [
                'describe applications of frictional force',
                'calculate frictional force',
            ]),
            ('20.3.3.7', 'Terminal velocity', [
                'explain terminal velocity',
                'describe falling of objects in vacuum and in fluids',
            ]),
            ('20.3.3.8', "Hooke's law", [
                'explain the effects of force',
                'verify Hooke\'s law experimentally',
                'plot and interpret extension-load graphs',
            ]),
            ('20.3.3.9', 'Uniform circular motion', [
                'differentiate angular displacement and angular velocity',
                'solve problems involving uniform circular motion',
            ]),
            ('20.3.3.10', 'Moments of forces', [
                'state the principle of moments',
                'carry out an experiment to verify the principle of moments',
                'determine centre of mass',
            ]),
        ]),
        ('20.3.4', 'Electricity and Magnetism', [
            ('20.3.4.1', 'Current electricity', [
                'define the internal resistance of a cell',
                'explain electrical hazards and safety',
                'carry out experiments on factors affecting resistance',
                'calculate the cost of electrical energy',
            ]),
            ('20.3.4.2', 'Magnetism and Electromagnetism', [
                'state laws of electromagnetic induction',
                'explain the working of ac and dc generators',
                'describe the working of a dc motor and a transformer',
            ]),
            ('20.3.4.3', 'Introduction to digital electronics', [
                'identify electric circuit symbols for electronic devices',
                'explain the difference between intrinsic and extrinsic semiconductors',
                'construct truth tables of logic gates',
            ]),
        ]),
        ('20.3.5', 'Oscillations and Waves', [
            ('20.3.5.1', 'Oscillations and waves', [
                'differentiate transverse and longitudinal waves',
                'explain amplitude, displacement, period and frequency',
                'explain wave properties',
                'derive the relation v = fλ',
            ]),
            ('20.3.5.2', 'Sound', [
                'explain transmission of sound in gases, liquids and solids',
                'describe experiments to show sound is produced by vibration',
                'solve problems involving velocity of sound',
            ]),
            ('20.3.5.3', 'Electromagnetic waves', [
                'state sources of electromagnetic waves',
                'describe the electromagnetic spectrum',
                'apply wave equation to solve problems',
            ]),
            ('20.3.5.4', 'Light and Lenses', [
                'state similarities and differences of a camera and a human eye',
                'explain image formation by converging lens',
                'derive the lens formula',
            ]),
        ]),
        ('20.3.6', 'Nuclear Physics', [
            ('20.3.6.1', 'Isotopes', [
                'define isotopes',
                'describe the nuclear structure of an atom',
                'represent the nucleus using nuclear notation',
            ]),
            ('20.3.6.2', 'Radioactivity', [
                'define radioactivity, nuclear fission and fusion',
                'state dangers of radioactive emissions',
                'solve problems involving half-life of isotopes',
                'balance nuclear equations',
            ]),
        ]),
    ],

    # ---- M182 Religious and Moral Education (MANEB 2020 §21.3) ----
    'M182': [
        ('21.3.1', 'Religion and development', [
            ('21.3.1.1', 'Religion and development', [
                'identify contributions of society to an individual',
                'state ways through which religions act as agents of development',
            ]),
            ('21.3.1.2', 'Religious teachings on contemporary issues', [
                'define contemporary issues',
                'identify teachings of Christianity, Islam and ATRs',
            ]),
            ('21.3.1.3', 'Religious teachings on conservation of the environment', [
                'state ways of overcoming challenges of the initiatives',
                'discuss the initiatives of the three major religions',
            ]),
            ('21.3.1.4', 'Religious teachings on drug and substance abuse', [
                'identify the teachings and initiatives',
                'explain the effects of drug abuse on the family and society',
            ]),
            ('21.3.1.5', 'Religious teachings on conflict resolution', [
                'give causes of religious conflicts',
                'identify the teachings and initiatives on conflict resolution',
            ]),
            ('21.3.1.6', 'Influence of culture on the three major religions', [
                'state causes of conflicts between religion and culture',
                'discuss the influence of culture',
            ]),
            ('21.3.1.7', 'Religious teachings on gender', [
                'identify teachings on inheritance in relation to gender',
                'discuss prejudice and discrimination',
            ]),
        ]),
        ('21.3.2', 'Moral values and teachings', [
            ('21.3.2.1', 'Moral values in the three major religions', [
                'identify moral values in Christianity, Islam and ATRs',
                'classify moral values into personal, social and global perspectives',
            ]),
            ('21.3.2.2', 'Death rituals', [
                'state death rituals in Islam',
                'explain death rituals in Christianity, Islam and ATRs',
            ]),
            ('21.3.2.3', 'Religious diversity and tolerance', [
                'define religious diversity',
                'discuss the importance of tolerance at family, national and global levels',
            ]),
        ]),
        ('21.3.3', 'Concepts of Religion and its moral dimension', [
            ('21.3.3.1', 'Moderation and self control', [
                'identify the teachings on self control and moderation',
            ]),
            ('21.3.3.2', 'Religious teachings on co-existence, transformation and tolerance', [
                'mention ways religions bridge the gap between rich and poor',
                'discuss the needs of the poor',
            ]),
        ]),
        ('21.3.4', 'Awareness of God', [
            ('21.3.4.1', 'Functions of spirits', [
                'give the functions of spirits in Islam and ATR',
                'identify the functions of spirits in Christianity',
            ]),
            ('21.3.4.2', 'Functions of saints, angels and good ancestral spirits', [
                'define saints, angels and good ancestral spirits',
                'discuss their functions',
            ]),
        ]),
        ('21.3.5', 'Communication with God in religions', [
            ('21.3.5.1', 'Intermediaries', [
                'mention intermediaries in Christianity and ATRs',
                'classify intermediaries according to each religion',
            ]),
        ]),
    ],

    # ---- M199 Social Affairs (MANEB 2020 §22.3) ----
    'M199': [
        ('22.3.1', 'People and the Environment', [
            ('22.3.1.1', 'Blood Donation', [
                'mention expectations of a blood donor',
                'describe qualities of a blood donor',
                'explain the importance of donating blood',
            ]),
            ('22.3.1.2', 'Use and Abuse of Prescribed Drugs', [
                'identify types of prescribed drugs',
                'explain causes of drug and substance abuse',
                'analyse the impact of drug abuse on development',
            ]),
            ('22.3.1.3', 'Non-Communicable Diseases', [
                'identify types of non-communicable diseases',
                'explain ways of preventing them',
            ]),
            ('22.3.1.4', 'Sexually Transmitted Infections and HIV and AIDS', [
                'define stigma and self-discrimination',
                'list rights of people living with HIV and AIDS',
                'analyse consequences of lack of guidance',
            ]),
            ('22.3.1.5', 'Effects of Sexual Identity on Behaviour', [
                'identify skills to overcome challenges of sexuality',
            ]),
            ('22.3.1.6', 'Sexual Reproductive Health and Human Behaviour', [
                'explain ways of avoiding reproductive health challenges',
            ]),
            ('22.3.1.7', 'Sexual Harassment', [
                'state the importance of reporting cases of harassment',
                'identify skills to help victims',
            ]),
            ('22.3.1.8', 'Population Change', [
                'describe characteristics of population change',
                'explain the effects of population growth',
            ]),
            ('22.3.1.9', 'Population Policy', [
                'identify key elements of population policy of Malawi',
                'discuss strategies for its implementation',
            ]),
            ('22.3.1.10', 'Population Growth', [
                'define population control',
                'identify ways in which nature and humans control population',
            ]),
            ('22.3.1.11', 'Disaster Risk Management', [
                'define disaster risk and disaster risk management',
                'identify common disasters affecting Malawi',
                'discuss preventive and mitigation measures',
            ]),
            ('22.3.1.12', 'Responsible Parenthood', [
                'define responsible parenthood',
                'describe qualities of responsible parenthood',
            ]),
        ]),
        ('22.3.2', 'Culture and Change', [
            ('22.3.2.1', 'Western and Eastern Cultures', [
                'identify different cultures and religions',
                'analyse impact of western and eastern cultures',
            ]),
            ('22.3.2.2', 'Cultural Preservation', [
                'define cultural preservation and heritage',
                'explain the relationship between culture and development',
            ]),
            ('22.3.2.3', 'Prejudice and Discrimination', [
                'identify causes of prejudice and discrimination',
                'examine their effects',
            ]),
            ('22.3.2.4', 'Gender issues in Malawi', [
                'identify laws and policies that are gender biased',
                'describe conventions on gender in Malawi',
            ]),
            ('22.3.2.5', 'Gender and Development', [
                'define gender platform of action',
                'analyse role of gender platform in promoting gender balance',
            ]),
            ('22.3.2.6', 'Gender issues in Africa', [
                'identify gender issues in Africa',
                'analyse case studies on achieving gender balance',
            ]),
            ('22.3.2.7', 'Courtship and Marriage', [
                'define courtship and marriage',
                'identify factors which help to preserve marriage',
            ]),
            ('22.3.2.8', 'Multiculturalism', [
                'define multiculturalism',
                'explain its impact on development',
            ]),
            ('22.3.2.9', 'Discrimination', [
                'define discrimination',
                'discuss efforts being put in place to curb discrimination',
            ]),
            ('22.3.2.10', 'Morals and Values', [
                'identify personal, family, national and international values',
                'explain ways of promoting family and community values',
            ]),
            ('22.3.2.11', 'Social and Moral Responsibilities', [
                'identify factors that influence peaceful co-existence',
                'describe social and moral responsibilities',
            ]),
            ('22.3.2.12', 'Cultural Practices, Gender and HIV and AIDS', [
                'identify cultural practices that put people at risk',
                'discuss ways of discouraging harmful cultural practices',
            ]),
        ]),
        ('22.3.3', 'Sustainable Development', [
            ('22.3.3.1', 'Employment', [
                'define pension', 'state different types of pension',
                'explain conditions for accessing pension benefits',
            ]),
            ('22.3.3.2', 'Development', [
                'identify aspects and indicators of development',
                'analyse social development initiatives',
            ]),
            ('22.3.3.3', 'Socio-Economic Problems', [
                'define socio-economic problems',
                'explain causes and effects of devaluation and over-indebtedness',
            ]),
            ('22.3.3.4', 'Interdependence in the Ecosystem', [
                'identify cases of interdependence',
                'explain how living and non-living things depend on each other',
            ]),
            ('22.3.3.5', 'People and the Environment', [
                'analyse effects of positive and negative attitudes towards environment',
            ]),
            ('22.3.3.6', 'Sustainable Development', [
                'define sustainable development',
                'describe essential conditions for sustainable development',
            ]),
            ('22.3.3.7', 'Developing Nations', [
                'define developing nation',
                'describe common characteristics of developing nations',
            ]),
            ('22.3.3.8', 'International Labour Laws', [
                'identify key elements of international labour laws',
                'discuss the importance of international labour laws',
            ]),
            ('22.3.3.9', 'Economic Policies', [
                'define economic policy and economic sustainability',
                'discuss the importance of economic policies',
            ]),
            ('22.3.3.10', 'Personal Finances', [
                'define personal finances',
                'describe ways of managing personal finances',
            ]),
            ('22.3.3.11', 'Financial Institutions', [
                'define financial institution and market forces',
                'identify financial institutions in Malawi',
                'analyse contributions of financial institutions to Malawi',
            ]),
            ('22.3.3.12', 'Business Values and Ethics', [
                'define business values and ethics',
                'describe corrupt practices in business',
                'explain business social responsibility',
            ]),
            ('22.3.3.13', 'Managing a Business Venture', [
                'identify key issues in financial management',
                'explain different types of taxes to be paid in business',
            ]),
            ('22.3.3.14', 'Risk taking and Creativity in Business', [
                'define risk taking in business',
                'describe skills for mitigating business risks',
            ]),
            ('22.3.3.15', 'Job Searching Strategies', [
                'describe job seeking strategies',
            ]),
            ('22.3.3.16', 'Saving Culture', [
                'define saving culture',
                'describe different ways of saving',
            ]),
        ]),
        ('22.3.4', 'Growth and Personal Development', [
            ('22.3.4.1', 'Self esteem', [
                'identify factors affecting self-esteem',
                'explain ways of building one\'s self esteem',
            ]),
            ('22.3.4.2', 'Time Management', [
                'state the importance of time management',
                'explain ways of managing time effectively',
            ]),
            ('22.3.4.3', 'Career Planning', [
                'identify sources of information about careers',
                'describe ways of preparing for job interviews',
            ]),
            ('22.3.4.4', 'Challenges associated with Adolescents', [
                'describe ways of coping with peer pressure',
                'explain the influence of media on adolescent behaviour',
            ]),
        ]),
        ('22.3.5', 'Global issues and Development', [
            ('22.3.5.1', 'Global issues and challenges', [
                'identify global challenges of the 21st century',
                'discuss the implications on development',
            ]),
            ('22.3.5.2', 'World Cooperation', [
                'identify areas of world cooperation',
                'describe factors that foster world cooperation',
            ]),
        ]),
        ('22.3.6', 'Civic Participation and Development', [
            ('22.3.6.1', 'Rights of Special Groups', [
                'describe the rights of special groups',
                'analyse ways of promoting social justice',
            ]),
            ('22.3.6.2', 'Public Space and Human Rights', [
                'define public space',
                'analyse case studies in relation to public space',
            ]),
            ('22.3.6.3', 'International Conventions on Human Rights', [
                'describe conventions for protecting human rights',
            ]),
            ('22.3.6.4', 'Taxation', [
                'define tax exemption, tax incentives and tax agreement',
            ]),
            ('22.3.6.5', 'Government of Malawi', [
                'describe composition of the government of Malawi',
                'explain how central and local government source revenue',
            ]),
            ('22.3.6.6', 'Good Governance', [
                'identify principles of good governance',
                'describe roles of institutions that enhance good governance',
            ]),
            ('22.3.6.7', 'Elections', [
                'describe the electoral process in Malawi',
                'analyse duties and functions of the Electoral Commission',
            ]),
            ('22.3.6.8', 'Peaceful Coexistence', [
                'identify forms of violence',
                'describe ways of preventing violence',
            ]),
            ('22.3.6.9', 'International Conflicts', [
                'describe causes of international conflicts',
                'analyse case studies on international conflicts',
            ]),
            ('22.3.6.10', 'International Peace Initiatives', [
                'identify international peace initiatives',
                'explain their successes and failures',
            ]),
            ('22.3.6.11', 'Refugee Crises', [
                'define refugee, asylum seeker and stateless person',
                'discuss the impact of refugees in the world',
            ]),
            ('22.3.6.12', 'Security', [
                'define security',
                'describe roles of the army and police in security',
            ]),
            ('22.3.6.13', 'Corruption and the Law', [
                'describe establishment of the Anti-Corruption Bureau',
                'explain the roles of the public in curbing corruption',
            ]),
            ('22.3.6.14', 'Social injustice', [
                'identify organisations that promote social justice',
                'analyse case studies of social injustice',
            ]),
            ('22.3.6.15', 'Social Services', [
                'define community participation',
                'analyse provision and care of social services',
            ]),
            ('22.3.6.16', 'Climate Change', [
                'describe the socio-economic impact of climate change',
            ]),
            ('22.3.6.17', 'Unions and Associations', [
                'identify unions and associations',
                'discuss the benefits of joining unions',
            ]),
            ('22.3.6.18', 'International Organisations that foster development', [
                'identify international organisations',
                'describe types of development work they undertake',
            ]),
        ]),
    ],

    # ---- M201 Technical Drawing (MANEB 2020 §23.3) ----
    'M201': [
        ('23.3.1', 'Drawing and Design', [
            ('23.3.1.1', 'Drawing Instruments and Materials', [
                'identify drawing instruments and materials',
                'use drawing instruments correctly',
            ]),
            ('23.3.1.2', 'Geometrical Constructions', [
                'construct bisectors, perpendiculars and polygons',
                'draw loci', 'apply tangency principles',
            ]),
            ('23.3.1.3', 'Orthographic Projection', [
                'draw orthographic views of objects',
                'apply first and third angle projection',
            ]),
            ('23.3.1.4', 'Pictorial Drawing', [
                'draw isometric, oblique and perspective views',
            ]),
            ('23.3.1.5', 'Sectional Views', [
                'draw sectional views and apply conventions',
            ]),
            ('23.3.1.6', 'Dimensioning', [
                'apply dimensioning conventions',
            ]),
        ]),
        ('23.3.2', 'Production Drawings', [
            ('23.3.2.1', 'Working Drawings', [
                'read and interpret working drawings',
                'produce working drawings according to BS 8888',
            ]),
            ('23.3.2.2', 'Assembly Drawings', [
                'read and produce assembly drawings',
            ]),
            ('23.3.2.3', 'Computer Aided Design (CAD)', [
                'use CAD software to produce technical drawings',
            ]),
        ]),
    ],

    # ---- M231 Woodwork (MANEB 2020 §24.3) ----
    'M231': [
        ('24.3.1', 'Production Technology', [
            ('24.3.1.1', 'Safety', [
                'discuss general safety in a woodwork workshop',
                'describe safe use of hand and machine tools',
            ]),
            ('24.3.1.2', 'Materials', [
                'describe working characteristics of wood',
                'identify types and uses of timber',
            ]),
            ('24.3.1.3', 'Hand Tools and Processes', [
                'identify hand tools and their uses',
                'carry out marking out, sawing, planing and chiselling',
            ]),
            ('24.3.1.4', 'Machine Tools and Processes', [
                'identify machine tools and their uses',
                'describe operations on woodworking machines',
            ]),
            ('24.3.1.5', 'Joints and Fastenings', [
                'identify common woodwork joints',
                'describe the production of common joints',
            ]),
            ('24.3.1.6', 'Wood Finishing', [
                'describe types of wood finishes',
                'explain methods of finishing wood',
            ]),
        ]),
        ('24.3.2', 'Design Process and Realisation', [
            ('24.3.2.1', 'The Design Process', [
                'develop a design brief and situation',
                'produce working drawings',
                'produce and evaluate a woodwork artifact',
            ]),
        ]),
        ('24.3.3', 'Entrepreneurship', [
            ('24.3.3.1', 'Marketing', [
                'define marketing terms in relation to woodwork',
                'describe marketing processes',
            ]),
            ('24.3.3.2', 'Resource Management', [
                'define terms used in resource management',
                'describe financial resource management',
            ]),
            ('24.3.3.3', 'Costing and Pricing', [
                'define direct and indirect costs',
                'explain factors that affect cost and price of woodwork products',
            ]),
        ]),
    ],

    # ===================== JCE (Forms 1-2) =====================

    # ---- J052 English (JCE) ----
    'J052': [
        ('J-GRAM', 'Grammar and Usage', [
            ('J-GRAM-01', 'Parts of Speech', [
                'identify nouns, pronouns, verbs, adjectives, adverbs, prepositions and conjunctions',
                'use parts of speech correctly in sentences',
            ]),
            ('J-GRAM-02', 'Tenses and Aspects', [
                'use present, past and future tenses correctly',
                'use perfect and continuous aspects',
            ]),
            ('J-GRAM-03', 'Sentence Structure', [
                'form simple, compound and complex sentences',
                'identify subject, verb and object',
            ]),
            ('J-GRAM-04', 'Punctuation', [
                'use full stops, commas, quotation marks and apostrophes correctly',
            ]),
            ('J-GRAM-05', 'Vocabulary', [
                'use synonyms and antonyms correctly',
                'form new words using prefixes and suffixes',
            ]),
        ]),
        ('J-COMP', 'Composition', [
            ('J-COMP-01', 'Narrative Writing', ['write a narrative essay']),
            ('J-COMP-02', 'Descriptive Writing', ['write a descriptive essay']),
            ('J-COMP-03', 'Letter Writing', [
                'write a friendly letter', 'write a formal letter',
            ]),
            ('J-COMP-04', 'Speech Writing', ['write a speech on a given topic']),
        ]),
        ('J-READ', 'Reading and Comprehension', [
            ('J-READ-01', 'Comprehension', [
                'answer questions based on a passage',
                'make inferences from a passage',
            ]),
            ('J-READ-02', 'Summary', ['summarise a passage in own words']),
            ('J-READ-03', 'Note-making', ['make notes from a passage']),
        ]),
        ('J-LIT', 'Literature', [
            ('J-LIT-01', 'Poetry', [
                'identify literary devices in poems',
                'explain the meaning of a poem',
            ]),
            ('J-LIT-02', 'Short Stories', [
                'identify plot, setting, characters and theme',
            ]),
            ('J-LIT-03', 'Novels and Plays', [
                'analyse character, theme and plot in prescribed texts',
            ]),
        ]),
    ],

    # ---- J032 Chichewa (JCE) ----
    'J032': [
        ('J-CHI-MAL', 'Malamulo a Chiyankhulo', [
            ('J-CHI-MAL-01', 'Mayina ndi Aneni', [
                'kuzindikira magulu a mayina',
                'kugwiritsa ntchito aneni moyenera',
            ]),
            ('J-CHI-MAL-02', 'Nthawi za Aneni', [
                'kugwiritsa ntchito nthawi zosiyanasiyana',
            ]),
            ('J-CHI-MAL-03', 'Zizindikiro za Mkalembedwe', [
                'kugwiritsa ntchito zizindikiro za mkalembedwe',
            ]),
        ]),
        ('J-CHI-LEM', 'Kulemba', [
            ('J-CHI-LEM-01', 'Chimangirizo', [
                'kulemba chimangirizo pa mutu woperekedwa',
            ]),
            ('J-CHI-LEM-02', 'Kalata', [
                'kulemba kalata yamchezo ndi yantchito',
            ]),
            ('J-CHI-LEM-03', 'Chifupikitso', [
                'kulemba chifupikitso cha nkhani',
            ]),
        ]),
        ('J-CHI-WER', 'Kuwerenga ndi Kumvetsa', [
            ('J-CHI-WER-01', 'Kumvetsa Nkhani', [
                'kuyankha mafunso okhudza nkhani',
            ]),
            ('J-CHI-WER-02', 'Ndakatulo', [
                'kufotokoza tanthauzo la ndakatulo',
                'kuzindikira zipangizo za ndakatulo',
            ]),
            ('J-CHI-WER-03', 'Nkhani Zazifupi', [
                'kufotokoza mfundo zikuluzikulu',
                'kuzindikira apangankhani',
            ]),
        ]),
    ],

    # ---- J131 Mathematics (JCE) ----
    'J131': [
        ('J-MATH-01', 'Number', [
            ('J-MATH-01-01', 'Number Systems', [
                'identify natural numbers, integers and rational numbers',
                'perform operations on directed numbers',
            ]),
            ('J-MATH-01-02', 'Fractions, Decimals and Percentages', [
                'convert between fractions, decimals and percentages',
                'solve problems involving percentages',
            ]),
            ('J-MATH-01-03', 'Factors and Multiples', [
                'find HCF and LCM', 'find squares and square roots',
            ]),
            ('J-MATH-01-04', 'Ratios and Proportions', [
                'solve problems involving ratio and proportion',
            ]),
            ('J-MATH-01-05', 'Indices', [
                'apply laws of indices',
            ]),
        ]),
        ('J-MATH-02', 'Algebra', [
            ('J-MATH-02-01', 'Algebraic Expressions', [
                'simplify algebraic expressions',
                'expand and factorise simple expressions',
            ]),
            ('J-MATH-02-02', 'Linear Equations', [
                'solve linear equations in one variable',
                'solve simultaneous linear equations',
            ]),
            ('J-MATH-02-03', 'Inequalities', [
                'solve simple linear inequalities',
            ]),
            ('J-MATH-02-04', 'Variations', [
                'solve direct and inverse variation problems',
            ]),
        ]),
        ('J-MATH-03', 'Geometry', [
            ('J-MATH-03-01', 'Angles and Polygons', [
                'calculate angles in polygons',
            ]),
            ('J-MATH-03-02', 'Triangles and Congruence', [
                'apply congruence and similarity',
                'use Pythagoras theorem',
            ]),
            ('J-MATH-03-03', 'Circles', [
                'calculate circumference and area of a circle',
            ]),
            ('J-MATH-03-04', 'Geometrical Constructions', [
                'construct angles, triangles and circles',
            ]),
        ]),
        ('J-MATH-04', 'Measurement', [
            ('J-MATH-04-01', 'Perimeter and Area', [
                'calculate perimeter and area of plane shapes',
            ]),
            ('J-MATH-04-02', 'Surface Area and Volume', [
                'calculate surface area and volume of solids',
            ]),
        ]),
        ('J-MATH-05', 'Statistics and Probability', [
            ('J-MATH-05-01', 'Data Representation', [
                'represent data using tables, bar charts and pie charts',
            ]),
            ('J-MATH-05-02', 'Measures of Central Tendency', [
                'calculate mean, median and mode',
            ]),
            ('J-MATH-05-03', 'Probability', [
                'calculate simple probability',
            ]),
        ]),
    ],

    # ---- J100 Integrated Science (JCE) ----
    'J100': [
        ('J-SCI-01', 'Biology', [
            ('J-SCI-01-01', 'Cells and Living Things', [
                'identify parts of a cell',
                'distinguish plants from animals',
            ]),
            ('J-SCI-01-02', 'Human Body Systems', [
                'describe the digestive, circulatory and respiratory systems',
            ]),
            ('J-SCI-01-03', 'Health and Disease', [
                'identify communicable and non-communicable diseases',
                'describe prevention measures',
            ]),
            ('J-SCI-01-04', 'Ecology', [
                'describe food chains and food webs',
                'explain interdependence in ecosystems',
            ]),
        ]),
        ('J-SCI-02', 'Chemistry', [
            ('J-SCI-02-01', 'Matter and its Properties', [
                'describe states of matter', 'identify physical and chemical changes',
            ]),
            ('J-SCI-02-02', 'Elements, Compounds and Mixtures', [
                'distinguish elements, compounds and mixtures',
                'separate mixtures by physical means',
            ]),
            ('J-SCI-02-03', 'Acids, Bases and Salts', [
                'identify acids, bases and salts',
                'describe neutralisation reactions',
            ]),
            ('J-SCI-02-04', 'Air and Water', [
                'describe composition of air',
                'explain the water cycle',
            ]),
        ]),
        ('J-SCI-03', 'Physics', [
            ('J-SCI-03-01', 'Measurement', [
                'measure length, mass, time and temperature',
                'use SI units',
            ]),
            ('J-SCI-03-02', 'Forces and Motion', [
                'describe types of forces',
                'explain speed, velocity and acceleration',
            ]),
            ('J-SCI-03-03', 'Energy', [
                'identify forms of energy',
                'describe energy transformations',
            ]),
            ('J-SCI-03-04', 'Electricity and Magnetism', [
                'construct simple circuits',
                'describe magnetic properties',
            ]),
        ]),
    ],

    # ---- J120 Social and Development Studies (JCE) ----
    'J120': [
        ('J-SDS-01', 'Citizenship', [
            ('J-SDS-01-01', 'Rights and Responsibilities', [
                'identify rights and responsibilities of citizens',
            ]),
            ('J-SDS-01-02', 'Democratic Governance', [
                'describe democratic principles',
                'explain roles of institutions in a democracy',
            ]),
            ('J-SDS-01-03', 'Peaceful Coexistence', [
                'explain ways of promoting peaceful coexistence',
            ]),
        ]),
        ('J-SDS-02', 'Development', [
            ('J-SDS-02-01', 'Meaning of Development', [
                'define development',
                'describe indicators of development',
            ]),
            ('J-SDS-02-02', 'Population and Development', [
                'describe population growth and its effects',
            ]),
            ('J-SDS-02-03', 'Sustainable Development', [
                'define sustainable development',
                'explain essential conditions for sustainable development',
            ]),
        ]),
        ('J-SDS-03', 'Environment', [
            ('J-SDS-03-01', 'Environmental Issues', [
                'identify environmental issues in Malawi',
                'describe ways of conserving the environment',
            ]),
            ('J-SDS-03-02', 'Disaster Management', [
                'identify common disasters in Malawi',
                'describe disaster risk management measures',
            ]),
        ]),
        ('J-SDS-04', 'Culture and Society', [
            ('J-SDS-04-01', 'Cultural Practices', [
                'identify cultural practices in Malawi',
                'discuss harmful and beneficial practices',
            ]),
            ('J-SDS-04-02', 'Gender Issues', [
                'identify gender issues in Malawi',
                'explain ways of achieving gender equity',
            ]),
        ]),
    ],

    # ---- J081 History (JCE) ----
    'J081': [
        ('J-HIS-01', 'Malawi History', [
            ('J-HIS-01-01', 'Pre-colonial Malawi', [
                'describe the early peoples of Malawi',
                'identify major migrations into Malawi',
            ]),
            ('J-HIS-01-02', 'Colonial Malawi', [
                'explain factors that led to British colonisation',
                'describe the Chilembwe uprising',
            ]),
            ('J-HIS-01-03', 'Road to Independence', [
                'describe the rise of nationalism in Nyasaland',
                'outline the key steps towards independence',
            ]),
        ]),
        ('J-HIS-02', 'African History', [
            ('J-HIS-02-01', 'Early African Civilisations', [
                'identify major African civilisations',
            ]),
            ('J-HIS-02-02', 'Slave Trade', [
                'describe the trans-Atlantic and Arab slave trade',
            ]),
            ('J-HIS-02-03', 'Scramble for Africa', [
                'explain causes and effects of the Scramble for Africa',
            ]),
        ]),
        ('J-HIS-03', 'World History', [
            ('J-HIS-03-01', 'World Wars', [
                'explain causes and effects of the two World Wars',
            ]),
            ('J-HIS-03-02', 'United Nations', [
                'state aims and structure of the UN',
            ]),
        ]),
    ],

    # ---- J073 Geography (JCE) ----
    'J073': [
        ('J-GEO-01', 'Map Work', [
            ('J-GEO-01-01', 'Map Reading', [
                'read and interpret map symbols',
                'measure distance and area on a map',
            ]),
            ('J-GEO-01-02', 'Scale and Gradient', [
                'calculate scale, gradient and cross sections',
            ]),
        ]),
        ('J-GEO-02', 'Physical Geography', [
            ('J-GEO-02-01', 'The Earth and its Structure', [
                'describe the internal structure of the earth',
            ]),
            ('J-GEO-02-02', 'Weather and Climate', [
                'describe elements of weather',
                'differentiate weather from climate',
            ]),
            ('J-GEO-02-03', 'Landforms', [
                'describe the formation of rivers, mountains and coastal landforms',
            ]),
        ]),
        ('J-GEO-03', 'Human Geography', [
            ('J-GEO-03-01', 'Population', [
                'describe population distribution and growth',
            ]),
            ('J-GEO-03-02', 'Agriculture', [
                'describe types of agriculture',
                'explain factors affecting agriculture',
            ]),
            ('J-GEO-03-03', 'Industry and Trade', [
                'describe types of industries',
                'explain the importance of trade',
            ]),
        ]),
    ],

    # ---- J182 Religious and Moral Education (JCE) ----
    'J182': [
        ('J-RME-01', 'Religion', [
            ('J-RME-01-01', 'Major Religions in Malawi', [
                'identify the major religions practised in Malawi',
                'describe key beliefs and practices',
            ]),
            ('J-RME-01-02', 'African Traditional Religion', [
                'describe beliefs and practices of ATR',
            ]),
            ('J-RME-01-03', 'Sacred Texts and Worship', [
                'identify sacred texts of major religions',
                'describe forms of worship',
            ]),
        ]),
        ('J-RME-02', 'Morality', [
            ('J-RME-02-01', 'Moral Values', [
                'identify moral values in different religions',
                'apply moral values to everyday situations',
            ]),
            ('J-RME-02-02', 'Family and Community', [
                'describe responsibilities within the family',
            ]),
        ]),
        ('J-RME-03', 'Contemporary Issues', [
            ('J-RME-03-01', 'HIV and AIDS', [
                'describe religious responses to HIV and AIDS',
            ]),
            ('J-RME-03-02', 'Environment', [
                'explain religious teachings on conservation of the environment',
            ]),
            ('J-RME-03-03', 'Drug and Substance Abuse', [
                'describe religious teachings on drug and substance abuse',
            ]),
        ]),
    ],

    # ---- J012 Agriculture (JCE) ----
    'J012': [
        ('J-AGR-01', 'Crop Production', [
            ('J-AGR-01-01', 'Soil', [
                'describe soil formation and properties',
                'explain ways of conserving soil',
            ]),
            ('J-AGR-01-02', 'Crop Husbandry', [
                'describe land preparation',
                'explain planting, weeding and harvesting practices',
            ]),
            ('J-AGR-01-03', 'Crop Protection', [
                'identify common crop pests and diseases',
                'describe control measures',
            ]),
        ]),
        ('J-AGR-02', 'Animal Production', [
            ('J-AGR-02-01', 'Livestock Keeping', [
                'identify common livestock in Malawi',
                'describe housing and feeding of livestock',
            ]),
            ('J-AGR-02-02', 'Animal Health', [
                'identify common livestock diseases and parasites',
                'describe control measures',
            ]),
        ]),
        ('J-AGR-03', 'Farm Management', [
            ('J-AGR-03-01', 'Farm Records and Budgeting', [
                'identify types of farm records',
                'prepare a simple farm budget',
            ]),
            ('J-AGR-03-02', 'Agricultural Marketing', [
                'describe marketing of agricultural produce',
            ]),
        ]),
    ],

    # ---- J023 Business Studies (JCE) ----
    'J023': [
        ('J-BUS-01', 'Trade', [
            ('J-BUS-01-01', 'Home Trade', [
                'define home trade',
                'describe the role of retailers and wholesalers',
            ]),
            ('J-BUS-01-02', 'Foreign Trade', [
                'differentiate imports and exports',
            ]),
            ('J-BUS-01-03', 'Aids to Trade', [
                'describe banking, insurance, transport and communication',
            ]),
        ]),
        ('J-BUS-02', 'Business Organisation', [
            ('J-BUS-02-01', 'Forms of Business', [
                'identify sole trader, partnership and companies',
            ]),
            ('J-BUS-02-02', 'Business Finance', [
                'identify sources of business finance',
            ]),
        ]),
        ('J-BUS-03', 'Entrepreneurship', [
            ('J-BUS-03-01', 'The Entrepreneur', [
                'identify qualities of an entrepreneur',
                'describe rewards and risks of entrepreneurship',
            ]),
            ('J-BUS-03-02', 'Small Business Management', [
                'describe steps in setting up a small business',
            ]),
            ('J-BUS-03-03', 'Marketing', [
                'define marketing mix',
                'describe channels of distribution',
            ]),
        ]),
        ('J-BUS-04', 'Business Calculations', [
            ('J-BUS-04-01', 'Profit, Loss and Interest', [
                'calculate profit, loss, simple and compound interest',
            ]),
            ('J-BUS-04-02', 'Taxes', [
                'identify types of taxes',
                'calculate VAT',
            ]),
        ]),
    ],

    # ---- J082 Home Economics (JCE) ----
    'J082': [
        ('J-HE-01', 'Food and Nutrition', [
            ('J-HE-01-01', 'Food Groups and Nutrients', [
                'identify food groups',
                'describe functions of nutrients',
            ]),
            ('J-HE-01-02', 'Food Preparation', [
                'describe methods of cooking',
                'prepare simple balanced meals',
            ]),
            ('J-HE-01-03', 'Food Hygiene and Preservation', [
                'describe food hygiene practices',
                'explain methods of food preservation',
            ]),
        ]),
        ('J-HE-02', 'Home Management', [
            ('J-HE-02-01', 'The Home and its Environment', [
                'describe ways of keeping the home clean',
            ]),
            ('J-HE-02-02', 'Family Resources', [
                'identify family resources',
                'explain ways of managing family resources',
            ]),
        ]),
        ('J-HE-03', 'Clothing and Textiles', [
            ('J-HE-03-01', 'Fibres and Fabrics', [
                'identify natural and synthetic fibres',
            ]),
            ('J-HE-03-02', 'Laundry and Care of Clothes', [
                'describe laundry processes',
                'mend clothing',
            ]),
            ('J-HE-03-03', 'Simple Garment Construction', [
                'take body measurements',
                'construct a simple garment',
            ]),
        ]),
        ('J-HE-04', 'Human Development', [
            ('J-HE-04-01', 'Growth and Development', [
                'describe stages of human development',
                'explain needs at each stage',
            ]),
            ('J-HE-04-02', 'Health and Safety', [
                'identify risks in the home',
                'describe safety measures',
            ]),
        ]),
    ],

    # ---- J015 Creative Arts (JCE) ----
    'J015': [
        ('J-CA-01', 'Visual Arts', [
            ('J-CA-01-01', 'Drawing and Painting', [
                'draw and shade simple objects',
                'paint simple compositions',
            ]),
            ('J-CA-01-02', 'Design and Lettering', [
                'produce simple posters and cards',
            ]),
            ('J-CA-01-03', 'Sculpture and Modelling', [
                'model simple objects using clay',
            ]),
        ]),
        ('J-CA-02', 'Performing Arts', [
            ('J-CA-02-01', 'Music', [
                'sing simple songs',
                'identify basic music notes',
            ]),
            ('J-CA-02-02', 'Drama', [
                'perform short plays',
            ]),
            ('J-CA-02-03', 'Dance', [
                'perform traditional and modern dances',
            ]),
        ]),
        ('J-CA-03', 'Craft', [
            ('J-CA-03-01', 'Weaving and Plaiting', [
                'produce simple woven items',
            ]),
            ('J-CA-03-02', 'Tie and Dye and Batik', [
                'produce simple tie and dye fabrics',
            ]),
            ('J-CA-03-03', 'Paper Craft', [
                'produce simple paper craft items',
            ]),
        ]),
    ],
}


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = 'Seed MANEB MSCE and JCE syllabus data into the database (idempotent).'

    def handle(self, *args, **options):
        self._seed_grade_scale()
        self._seed_sessions()
        subjects_by_code = self._seed_subjects(MSCE_SUBJECTS, 'MSCE')
        subjects_by_code.update(self._seed_subjects(JCE_SUBJECTS, 'JCE'))
        self._seed_topic_trees(subjects_by_code)
        self.stdout.write(self.style.SUCCESS(
            f'Syllabus seeded: {len(subjects_by_code)} subjects '
            f'({len(MSCE_SUBJECTS)} MSCE + {len(JCE_SUBJECTS)} JCE), '
            f'{len(TOPIC_TREES)} topic trees.'
        ))

    # -- helpers ----------------------------------------------------------

    def _seed_grade_scale(self):
        self.stdout.write('Seeding MANEB grade scale...')
        for num, label, gce, desc in MANEB_GRADE_SCALE:
            ManebGradeScale.objects.update_or_create(
                grade_number=num,
                defaults={'label': label, 'gce_equivalent': gce, 'description': desc},
            )

    def _seed_sessions(self):
        self.stdout.write('Creating exam sessions...')
        for name, year, level in EXAM_SESSIONS:
            ExamSession.objects.update_or_create(
                name=name,
                defaults={'exam_year': year, 'level': level, 'is_current': True},
            )

    def _seed_subjects(self, subject_rows, level):
        self.stdout.write(f'Seeding {level} subjects & papers...')
        by_code = {}
        for code, name, cat, elective, num_papers in subject_rows:
            subject, _ = Subject.objects.update_or_create(
                code=code,
                defaults={
                    'name': name, 'category': cat,
                    'is_elective': elective, 'level': level,
                },
            )
            by_code[code] = subject
            self._seed_papers(subject, name, num_papers)
            self._seed_descriptors(subject, name)
        return by_code

    def _seed_papers(self, subject, subject_name, num_papers):
        for i in range(1, num_papers + 1):
            Paper.objects.update_or_create(
                subject=subject, number=self._roman(i),
                defaults={
                    'paper_type': 'theory' if i == 1 else 'practical',
                    'duration_minutes': 120,
                    'total_marks': 100,
                },
            )

    def _seed_descriptors(self, subject, subject_name):
        # SY-18: minimal grade descriptors per subject.
        for band, text in [
            ('pass',       f'Candidates show a basic understanding of {subject_name} concepts.'),
            ('credit',     f'Candidates apply {subject_name} concepts to solve familiar problems.'),
            ('distinction', f'Candidates apply {subject_name} concepts to solve unfamiliar, complex problems.'),
        ]:
            GradeDescriptor.objects.update_or_create(
                subject=subject, paper=None, grade_band=band,
                defaults={'descriptor': text},
            )

    def _seed_topic_trees(self, subjects_by_code):
        self.stdout.write('Seeding topic trees...')
        for code, groups in TOPIC_TREES.items():
            subject = subjects_by_code.get(code)
            if not subject:
                self.stderr.write(f'  ! No subject for code {code}, skipping tree')
                continue
            self._seed_one_tree(subject, groups)

    def _seed_one_tree(self, subject, groups):
        """groups = [(parent_code, parent_title, [(child_code, child_title, [objectives]), ...]), ...]"""
        for order, (parent_code, parent_title, children) in enumerate(groups):
            parent, _ = SyllabusTopic.objects.update_or_create(
                subject=subject, code=parent_code,
                defaults={'title': parent_title, 'order': order, 'parent': None},
            )
            for child_order, child in enumerate(children):
                child_code, child_title = child[0], child[1]
                objectives = child[2] if len(child) > 2 else []
                child_topic, _ = SyllabusTopic.objects.update_or_create(
                    subject=subject, code=child_code,
                    defaults={'title': child_title, 'order': child_order, 'parent': parent},
                )
                for obj_order, obj_text in enumerate(objectives):
                    AssessmentObjective.objects.update_or_create(
                        topic=child_topic, text=obj_text,
                        defaults={'order': obj_order},
                    )

    @staticmethod
    def _roman(n):
        return {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}.get(n, str(n))