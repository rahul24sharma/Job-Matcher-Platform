from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.models import Job, Base
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample tech jobs with realistic requirements
SAMPLE_JOBS = [
    {
        "title": "Senior Full Stack Developer",
        "company": "TechCorp Solutions",
        "location": "Boston, MA",
        "description": "We're looking for a Senior Full Stack Developer to join our growing team. You'll work on cutting-edge web applications using modern technologies.",
        "required_skills": "Python,React,PostgreSQL,Docker,AWS,REST API,Git",
        "url": "https://example.com/jobs/1",
        "remote": True,
        "salary_min": 120000,
        "salary_max": 160000
    },
    {
        "title": "Python Backend Engineer",
        "company": "DataFlow Inc",
        "location": "New York, NY",
        "description": "Join our backend team to build scalable APIs and microservices. Experience with FastAPI and cloud services required.",
        "required_skills": "Python,FastAPI,PostgreSQL,Redis,Docker,Kubernetes,AWS",
        "url": "https://example.com/jobs/2",
        "remote": True,
        "salary_min": 110000,
        "salary_max": 150000
    },
    {
        "title": "React Frontend Developer",
        "company": "WebInnovate",
        "location": "San Francisco, CA",
        "description": "Create beautiful, responsive user interfaces with React and modern JavaScript. Experience with TypeScript is a plus.",
        "required_skills": "React,JavaScript,TypeScript,HTML,CSS,Webpack,Git,REST API",
        "url": "https://example.com/jobs/3",
        "remote": False,
        "salary_min": 100000,
        "salary_max": 140000
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudScale Systems",
        "location": "Seattle, WA",
        "description": "Automate infrastructure and improve deployment processes. Strong experience with cloud platforms and CI/CD required.",
        "required_skills": "Docker,Kubernetes,AWS,Terraform,Jenkins,Python,Linux,Git",
        "url": "https://example.com/jobs/4",
        "remote": True,
        "salary_min": 130000,
        "salary_max": 170000
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Innovations",
        "location": "Boston, MA",
        "description": "Build and deploy ML models at scale. Experience with deep learning frameworks and cloud ML platforms required.",
        "required_skills": "Python,TensorFlow,PyTorch,Scikit-learn,AWS,Docker,SQL,Git",
        "url": "https://example.com/jobs/5",
        "remote": False,
        "salary_min": 140000,
        "salary_max": 180000
    },
    {
        "title": "Junior Software Developer",
        "company": "StartupHub",
        "location": "Austin, TX",
        "description": "Great opportunity for recent graduates or junior developers. We'll help you grow your skills in a supportive environment.",
        "required_skills": "Python,JavaScript,Git,SQL,HTML,CSS",
        "url": "https://example.com/jobs/6",
        "remote": True,
        "salary_min": 70000,
        "salary_max": 90000
    },
    {
        "title": "Django Web Developer",
        "company": "WebCraft Studios",
        "location": "Chicago, IL",
        "description": "Build web applications using Django and PostgreSQL. Experience with REST APIs and frontend frameworks is a plus.",
        "required_skills": "Python,Django,PostgreSQL,JavaScript,HTML,CSS,Git,REST API",
        "url": "https://example.com/jobs/7",
        "remote": False,
        "salary_min": 95000,
        "salary_max": 125000
    },
    {
        "title": "Data Engineer",
        "company": "BigData Analytics",
        "location": "Boston, MA",
        "description": "Design and build data pipelines. Experience with big data technologies and cloud platforms required.",
        "required_skills": "Python,SQL,Apache Spark,Airflow,AWS,PostgreSQL,Docker",
        "url": "https://example.com/jobs/8",
        "remote": True,
        "salary_min": 115000,
        "salary_max": 155000
    },
    {
        "title": "Full Stack JavaScript Developer",
        "company": "NodeWorks",
        "location": "Denver, CO",
        "description": "Work with Node.js and React to build full-stack applications. Experience with MongoDB and GraphQL is desired.",
        "required_skills": "JavaScript,Node.js,React,MongoDB,Express,GraphQL,Git",
        "url": "https://example.com/jobs/9",
        "remote": True,
        "salary_min": 105000,
        "salary_max": 145000
    },
    {
        "title": "iOS Developer",
        "company": "MobileFirst Inc",
        "location": "San Francisco, CA",
        "description": "Develop native iOS applications using Swift. Experience with SwiftUI and Core Data required.",
        "required_skills": "Swift,iOS,Xcode,SwiftUI,Git,REST API,Core Data",
        "url": "https://example.com/jobs/10",
        "remote": False,
        "salary_min": 120000,
        "salary_max": 160000
    },
    {
        "title": "Android Developer",
        "company": "AppVentures",
        "location": "New York, NY",
        "description": "Build Android apps using Kotlin. Experience with Jetpack Compose and modern Android architecture.",
        "required_skills": "Kotlin,Android,Java,Android Studio,Git,REST API,Firebase",
        "url": "https://example.com/jobs/11",
        "remote": True,
        "salary_min": 110000,
        "salary_max": 150000
    },
    {
        "title": "Site Reliability Engineer",
        "company": "ReliableOps",
        "location": "Seattle, WA",
        "description": "Ensure high availability and performance of production systems. Strong Linux and automation skills required.",
        "required_skills": "Linux,Python,Kubernetes,Prometheus,Grafana,AWS,Terraform,Git",
        "url": "https://example.com/jobs/12",
        "remote": True,
        "salary_min": 125000,
        "salary_max": 165000
    },
    {
        "title": "Vue.js Frontend Developer",
        "company": "VueWorks",
        "location": "Portland, OR",
        "description": "Build modern web applications with Vue.js. Experience with Vuex and Nuxt.js preferred.",
        "required_skills": "Vue,JavaScript,HTML,CSS,Webpack,Git,REST API,TypeScript",
        "url": "https://example.com/jobs/13",
        "remote": False,
        "salary_min": 95000,
        "salary_max": 135000
    },
    {
        "title": "Senior Python Developer",
        "company": "PythonPros",
        "location": "Boston, MA",
        "description": "Lead Python development projects. Strong experience with async programming and microservices required.",
        "required_skills": "Python,FastAPI,PostgreSQL,Redis,Docker,RabbitMQ,Git,AWS",
        "url": "https://example.com/jobs/14",
        "remote": True,
        "salary_min": 130000,
        "salary_max": 170000
    },
    {
        "title": "Security Engineer",
        "company": "SecureNet",
        "location": "Washington, DC",
        "description": "Implement security best practices and conduct security assessments. Experience with cloud security required.",
        "required_skills": "Python,Linux,AWS,Docker,Kubernetes,Git,Terraform,Security",
        "url": "https://example.com/jobs/15",
        "remote": False,
        "salary_min": 135000,
        "salary_max": 175000
    },
    {
        "title": "GraphQL API Developer",
        "company": "APIFirst",
        "location": "San Francisco, CA",
        "description": "Design and implement GraphQL APIs. Experience with Apollo Server and microservices architecture.",
        "required_skills": "GraphQL,Node.js,TypeScript,PostgreSQL,Docker,Kubernetes,Git",
        "url": "https://example.com/jobs/16",
        "remote": True,
        "salary_min": 115000,
        "salary_max": 155000
    },
    {
        "title": "Flutter Mobile Developer",
        "company": "CrossPlatform Co",
        "location": "Miami, FL",
        "description": "Build cross-platform mobile apps with Flutter. Experience with state management and Firebase.",
        "required_skills": "Flutter,Dart,Firebase,Git,REST API,iOS,Android",
        "url": "https://example.com/jobs/17",
        "remote": True,
        "salary_min": 100000,
        "salary_max": 140000
    },
    {
        "title": "Blockchain Developer",
        "company": "CryptoTech",
        "location": "New York, NY",
        "description": "Develop smart contracts and blockchain applications. Experience with Ethereum and Solidity required.",
        "required_skills": "Blockchain,Solidity,JavaScript,Node.js,Web3,Git,React",
        "url": "https://example.com/jobs/18",
        "remote": True,
        "salary_min": 140000,
        "salary_max": 190000
    },
    {
        "title": "Junior Data Scientist",
        "company": "DataMind",
        "location": "Boston, MA",
        "description": "Entry-level position for data science enthusiasts. Strong Python and statistics background required.",
        "required_skills": "Python,Pandas,NumPy,Scikit-learn,SQL,Jupyter,Git",
        "url": "https://example.com/jobs/19",
        "remote": False,
        "salary_min": 80000,
        "salary_max": 110000
    },
    {
        "title": "Cloud Architect",
        "company": "CloudMasters",
        "location": "Seattle, WA",
        "description": "Design cloud infrastructure solutions. Multi-cloud experience and architecture certifications preferred.",
        "required_skills": "AWS,Azure,Terraform,Docker,Kubernetes,Python,Linux,Git",
        "url": "https://example.com/jobs/20",
        "remote": True,
        "salary_min": 150000,
        "salary_max": 200000
    },
    {
        "title": "React Native Developer",
        "company": "MobileHub",
        "location": "Los Angeles, CA",
        "description": "Build mobile apps with React Native. Experience with native modules and app deployment required.",
        "required_skills": "React Native,JavaScript,React,Git,REST API,iOS,Android,Redux",
        "url": "https://example.com/jobs/21",
        "remote": True,
        "salary_min": 110000,
        "salary_max": 150000
    },
    {
        "title": "Database Administrator",
        "company": "DataSafe Corp",
        "location": "Houston, TX",
        "description": "Manage and optimize database systems. Experience with PostgreSQL and MongoDB required.",
        "required_skills": "PostgreSQL,MongoDB,SQL,Linux,Python,AWS,Redis,Git",
        "url": "https://example.com/jobs/22",
        "remote": False,
        "salary_min": 95000,
        "salary_max": 130000
    },
    {
        "title": "QA Automation Engineer",
        "company": "QualityFirst",
        "location": "Boston, MA",
        "description": "Build test automation frameworks. Experience with Selenium and API testing required.",
        "required_skills": "Python,Selenium,Jest,Cypress,Git,Jenkins,Docker,API Testing",
        "url": "https://example.com/jobs/23",
        "remote": True,
        "salary_min": 90000,
        "salary_max": 125000
    },
    {
        "title": "Rust Systems Developer",
        "company": "SystemCore",
        "location": "San Francisco, CA",
        "description": "Build high-performance systems in Rust. Experience with systems programming required.",
        "required_skills": "Rust,Linux,C++,Git,Docker,PostgreSQL,Redis",
        "url": "https://example.com/jobs/24",
        "remote": False,
        "salary_min": 130000,
        "salary_max": 170000
    },
    {
        "title": "Technical Lead - Full Stack",
        "company": "TechLeaders Inc",
        "location": "Boston, MA",
        "description": "Lead a team of developers. Strong technical skills and leadership experience required.",
        "required_skills": "Python,React,Node.js,PostgreSQL,AWS,Docker,Kubernetes,Git,Agile",
        "url": "https://example.com/jobs/25",
        "remote": True,
        "salary_min": 140000,
        "salary_max": 180000
    }
]

def seed_jobs(db: Session = None):
    """Seed sample jobs into the database"""
    if db is None:
        db = SessionLocal()
    
    try:
        # Check if jobs already exist
        existing_count = db.query(Job).count()
        if existing_count > 0:
            logger.info(f"Jobs already seeded. Found {existing_count} jobs.")
            return existing_count
        
        # Add jobs
        added_count = 0
        for i, job_data in enumerate(SAMPLE_JOBS, 1):
            # Create job
            job = Job(
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                description=job_data["description"],
                required_skills=job_data["required_skills"],
                url=job_data["url"],
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            # Add optional fields if they exist
            if "remote" in job_data:
                job.remote = job_data["remote"]
            if "salary_min" in job_data:
                job.salary_min = job_data["salary_min"]
            if "salary_max" in job_data:
                job.salary_max = job_data["salary_max"]
            
            db.add(job)
            added_count += 1
            
            if added_count % 5 == 0:
                logger.info(f"Added {added_count} jobs...")
        
        # Add more variations by slightly modifying existing jobs
        variations = [
            ("Junior", 0.7), ("Senior", 1.3), ("Lead", 1.5)
        ]
        
        for prefix, salary_multiplier in variations:
            for job_data in SAMPLE_JOBS[:10]:  # Create variations of first 10 jobs
                if "Junior" not in job_data["title"] and "Senior" not in job_data["title"]:
                    job = Job(
                        title=f"{prefix} {job_data['title']}",
                        company=f"{job_data['company']} ({prefix})",
                        location=job_data["location"],
                        description=f"{prefix} position. {job_data['description']}",
                        required_skills=job_data["required_skills"],
                        url=f"{job_data['url']}-{prefix.lower()}",
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    
                    if "salary_min" in job_data:
                        job.salary_min = int(job_data["salary_min"] * salary_multiplier)
                    if "salary_max" in job_data:
                        job.salary_max = int(job_data["salary_max"] * salary_multiplier)
                    
                    db.add(job)
                    added_count += 1
        
        db.commit()
        
        logger.info(f"✅ Successfully added {added_count} jobs to the database")
        
        # Show some statistics
        job_stats = db.query(Job).count()
        remote_jobs = db.query(Job).filter(Job.remote == True).count()
        
        logger.info(f"📊 Job Statistics:")
        logger.info(f"  Total jobs: {job_stats}")
        logger.info(f"  Remote jobs: {remote_jobs}")
        logger.info(f"  On-site jobs: {job_stats - remote_jobs}")
        
        return added_count
        
    except Exception as e:
        logger.error(f"❌ Error seeding jobs: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def get_job_stats(db: Session = None):
    """Get statistics about jobs in database"""
    if db is None:
        db = SessionLocal()
    
    try:
        from sqlalchemy import func
        
        # Total jobs
        total = db.query(func.count(Job.id)).scalar()
        
        # Jobs by location
        locations = db.query(
            Job.location,
            func.count(Job.id)
        ).group_by(Job.location).all()
        
        # Salary ranges
        avg_min = db.query(func.avg(Job.salary_min)).scalar()
        avg_max = db.query(func.avg(Job.salary_max)).scalar()
        
        logger.info(f"\n📊 Job Database Statistics:")
        logger.info(f"Total jobs: {total}")
        logger.info(f"\nJobs by location:")
        for loc, count in locations[:5]:
            logger.info(f"  {loc}: {count}")
        logger.info(f"\nSalary ranges:")
        logger.info(f"  Average minimum: ${avg_min:,.0f}")
        logger.info(f"  Average maximum: ${avg_max:,.0f}")
        
    finally:
        db.close()

if __name__ == "__main__":
    # Run this script directly to seed jobs
    logger.info("🌱 Starting job seeding process...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Seed jobs
    seed_jobs()
    
    # Show statistics
    get_job_stats()