import pandas as pd

names = [
    "Nakiri Ayame", "Himemori Luna", "Sakura Miko", "Fuwawa Abyssgard", "Moona Hoshinova",
    "Kureiji Ollie", "Akai Haato", "Yukihana Lamy", "Momosuzu Nene", "Elizabeth Rose Bloodflame",
    "Juufuutei Raden", "Mizumiya Su", "Nekomata Okayu", "Ninomae Ina'nis", "Shiori Novella",
    "Omaru Polka", "Kaela Kovalskia", "Hoshimachi Suisei", "[Alum] Ceres Fauna", "Usada Pekora",
    "[Alum] Nanashi Mumei", "[Alum] Murasaki Shion", "Isaki Riona", "Houshou Marine",
    "La+ Darknesss", "Harusaki Nodoka", "Anya Melfissa", "Otonose Kanade", "Ayunda Risu",
    "Yuzuki Choco", "Mori Calliope", "[Affiliate] Sakamata Chloe", "Hakos Baelz",
    "Ichijou Ririka", "Shirogane Noel", "Airani Iofifteen", "[Alum] Tsukumo Sana",
    "Shirakami Fubuki", "Inugami Korone", "Oozora Subaru", "Tokino Sora", "Raora Panthera",
    "Takanashi Kiara", "Ookami Mio", "Gigi Murin", "[Alum] Minato Aqua", "[Affiliate] Watson Amelia",
    "Robocosan", "Kobo Kanaeru", "[Alum] Gawr Gura", "Todoroki Hajime", "Mococo Abyssgard",
    "Aki Rosenthal", "Hiodoshi Ao", "Natsuiro Matsuri", "Hakui Koyori", "Nerissa Ravencroft",
    "Cecilia Immergreen", "Takane Lui", "Shishiro Botan", "Kazama Iroha", "Koseki Bijou",
    "[Retirement] Friend A (A-chan)", "Rindo Chihaya", "Shiranui Flare", "Kikirara Vivi",
    "Koganei Niko", "Ouro Kronii", "[Alum] Kiryu Coco", "Tsunomaki Watame", "Amane Kanata",
    "IRyS", "Pavolia Reine", "AZKi", "Vestia Zeta", "Tokoyami Towa"
]

handles = [
    "@NakiriAyame", "@HimemoriLuna", "@SakuraMiko", "@FUWAMOCOch", "@MoonaHoshinova",
    "@KureijiOllie", "@AkaiHaato", "@YukihanaLamy", "@MomosuzuNene", "@holoen_erbloodflame",
    "@JuufuuteiRaden", "@MizumiyaSu", "@NekomataOkayu", "@NinomaeInanis", "@ShioriNovella",
    "@OmaruPolka", "@KaelaKovalskia", "@HoshimachiSuisei", "@CeresFauna", "@usadapekora",
    "@NanashiMumei", "@MurasakiShion", "@IsakiRiona", "@HoushouMarine", "@LaplusDarknesss",
    "@holoANroom", "@AnyaMelfissa", "@OtonoseKanade", "@AyundaRisu", "@YuzukiChoco",
    "@MoriCalliope", "@SakamataChloe", "@HakosBaelz", "@IchijouRirika", "@ShiroganeNoel",
    "@AiraniIofifteen", "@TsukumoSana", "@ShirakamiFubuki", "@InugamiKorone", "@OozoraSubaru",
    "@TokinoSora", "@holoen_raorapanthera", "@TakanashiKiara", "@OokamiMio", "@holoen_gigimurin",
    "@MinatoAqua", "@WatsonAmelia", "@Robocosan", "@KoboKanaeru", "@GawrGura",
    "@TodorokiHajime", "@FUWAMOCOch", "@AkiRosenthal", "@HiodoshiAo", "@NatsuiroMatsuri",
    "@HakuiKoyori", "@NerissaRavencroft", "@holoen_ceciliaimmergreen", "@TakaneLui",
    "@ShishiroBotan", "@kazamairoha", "@KosekiBijou", "-", "@RindoChihaya", "@ShiranuiFlare",
    "@KikiraraVivi", "@KoganeiNiko", "@OuroKronii", "@KiryuCoco", "@TsunomakiWatame",
    "@AmaneKanata", "@IRyS", "@PavoliaReine", "@AZKi", "@VestiaZeta", "@TokoyamiTowa"
]

df = pd.DataFrame({
    "Name": names,
    "Handle": handles
})

df.to_csv("./data/intermediate.csv")
