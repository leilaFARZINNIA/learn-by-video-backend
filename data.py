import asyncio
from sqlalchemy.dialects.postgresql import insert
from db.postgres import engine, AsyncSessionLocal, Base
from models.course import CourseORM
from models.media import MediaORM

VID = {
    "bbb": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "ed": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
    "fbj": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
    "fbf": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
    "fbe": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "fbb": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "fbm": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
}

def long_transcript(topic: str, n: int = 12, step: int = 10):
    return [{"time": i * step, "text": f"{topic} — Part {i}"} for i in range(1, n + 1)]

COURSES = [
    {"course_id": "course_1", "course_title": "ReactNative (v)", "course_description": "Setup, core components, navigation, and APIs.", "course_type": "video"},
    {"course_id": "course_2", "course_title": "Flutter (v)", "course_description": "Widgets, state, navigation, networking.", "course_type": "video"},
    {"course_id": "course_3", "course_title": "SpringBoot (p)", "course_description": "Controllers, services, JPA, testing.", "course_type": "podcast"},
    {"course_id": "course_4", "course_title": "PythonDS (v)", "course_description": "NumPy, Pandas, Matplotlib, Scikit-learn basics.", "course_type": "video"},
    {"course_id": "course_5", "course_title": "DockerK8s (p)", "course_description": "Containers, orchestration, scaling apps.", "course_type": "podcast"},
    {"course_id": "course_6", "course_title": "DigTrans (t)", "course_description": "Cloud, AI, IoT, and security in modern enterprises.", "course_type": "text"},
]

MEDIAS = [
    # React Native
    {"media_id": "media_1", "media_title": "Setup (video)", "media_description": "Install Node, Android Studio/Xcode, create project.", "course_id": "course_1", "media_url": VID["bbb"], "media_transcript": long_transcript("Setup")},
    {"media_id": "media_2", "media_title": "Components (video)", "media_description": "View, Text, Image, ScrollView, FlatList.", "course_id": "course_1", "media_url": VID["ed"], "media_transcript": long_transcript("Components")},
    {"media_id": "media_3", "media_title": "Navigation (video)", "media_description": "React Navigation setup, stacks, params.", "course_id": "course_1", "media_url": VID["fbj"], "media_transcript": long_transcript("Navigation")},
    {"media_id": "media_4", "media_title": "Networking (video)", "media_description": "Fetch, Axios, error handling, pagination.", "course_id": "course_1", "media_url": VID["fbf"], "media_transcript": long_transcript("Networking")},

    # Flutter
    {"media_id": "media_5", "media_title": "Widgets (video)", "media_description": "Stateless vs Stateful, build method, layout.", "course_id": "course_2", "media_url": VID["fbe"], "media_transcript": long_transcript("Widgets")},
    {"media_id": "media_6", "media_title": "State (video)", "media_description": "setState, Provider, Riverpod overview.", "course_id": "course_2", "media_url": VID["fbb"], "media_transcript": long_transcript("State")},
    {"media_id": "media_7", "media_title": "Routes (video)", "media_description": "Navigator 1.0/2.0 concepts, named routes.", "course_id": "course_2", "media_url": VID["fbm"], "media_transcript": long_transcript("Routes")},

    # Spring Boot
    {"media_id": "media_8", "media_title": "Setup (podcast)", "media_description": "Spring Initializr, structure, devtools.", "course_id": "course_3", "media_url": VID["bbb"], "media_transcript": long_transcript("Setup")},
    {"media_id": "media_9", "media_title": "REST (podcast)", "media_description": "Controllers, DTOs, validation.", "course_id": "course_3", "media_url": VID["ed"], "media_transcript": long_transcript("REST")},
    {"media_id": "media_10", "media_title": "JPA (podcast)", "media_description": "Entities, repositories, relations.", "course_id": "course_3", "media_url": VID["fbj"], "media_transcript": long_transcript("JPA")},

    # Python for Data Science
    {"media_id": "media_11", "media_title": "NumPy (video)", "media_description": "Arrays, broadcasting, vectorized ops.", "course_id": "course_4", "media_url": VID["fbe"], "media_transcript": long_transcript("NumPy")},
    {"media_id": "media_12", "media_title": "Pandas (video)", "media_description": "Series, DataFrame, groupby, merge.", "course_id": "course_4", "media_url": VID["fbb"], "media_transcript": long_transcript("Pandas")},
    {"media_id": "media_13", "media_title": "Viz (video)", "media_description": "Matplotlib, Seaborn, Plotly intro.", "course_id": "course_4", "media_url": VID["fbm"], "media_transcript": long_transcript("Viz")},

    # Docker & Kubernetes
    {"media_id": "media_14", "media_title": "Images (podcast)", "media_description": "Build, tag, push images.", "course_id": "course_5", "media_url": VID["bbb"], "media_transcript": long_transcript("Images")},
    {"media_id": "media_15", "media_title": "Compose (podcast)", "media_description": "Multi-container setup.", "course_id": "course_5", "media_url": VID["ed"], "media_transcript": long_transcript("Compose")},
    {"media_id": "media_16", "media_title": "K8s (podcast)", "media_description": "Pods, Deployments, Services.", "course_id": "course_5", "media_url": VID["fbj"], "media_transcript": long_transcript("K8s")},

    # Digital Transformation
    {"media_id": "media_17", "media_title": "Cloud (text)", "media_description": "IaaS, PaaS, SaaS explained.", "course_id": "course_6", "media_url": "", "media_transcript": long_transcript("Cloud")},
    {"media_id": "media_18", "media_title": "AI (text)", "media_description": "AI, ML, DL in enterprise.", "course_id": "course_6", "media_url": "", "media_transcript": long_transcript("AI")},
    {"media_id": "media_19", "media_title": "IoT (text)", "media_description": "IoT devices, risks, and security.", "course_id": "course_6", "media_url": "", "media_transcript": long_transcript("IoT")},
]

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        for c in COURSES:
            stmt = insert(CourseORM).values(**c).on_conflict_do_nothing(index_elements=["course_id"])
            await session.execute(stmt)
        for m in MEDIAS:
            stmt = insert(MediaORM).values(**m).on_conflict_do_nothing(index_elements=["media_id"])
            await session.execute(stmt)
        await session.commit()

    print("✅ Seed inserted: 6 courses & 19 medias.")

if __name__ == "__main__":
    asyncio.run(main())
