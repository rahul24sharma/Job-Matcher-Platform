from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.models import SkillMaster, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comprehensive skill database with categories
SKILLS_DATA = {
    "language": [
        # Popular languages
        "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "Go", "Rust", 
        "Swift", "Kotlin", "Scala", "R", "PHP", "TypeScript", "Objective-C",
        "Dart", "Elixir", "Clojure", "Haskell", "Lua", "Perl", "Julia",
        "MATLAB", "Fortran", "COBOL", "Assembly", "Visual Basic", "F#",
        "Erlang", "OCaml", "Groovy", "PowerShell", "Bash", "Shell Script",
        "SQL", "PL/SQL", "T-SQL", "Solidity", "Verilog", "VHDL"
    ],
    
    "frontend_framework": [
        "React", "Angular", "Vue", "Vue.js", "Svelte", "Next.js", "Nuxt.js", 
        "Gatsby", "Ember.js", "Backbone.js", "Alpine.js", "Preact", "Lit",
        "Stimulus", "Meteor", "Polymer", "Aurelia", "Mithril", "Riot.js",
        "jQuery", "Bootstrap", "Tailwind CSS", "Material-UI", "Ant Design",
        "Chakra UI", "Semantic UI", "Foundation", "Bulma", "Styled Components",
        "CSS", "HTML", "HTML5", "CSS3", "Sass", "SCSS", "Less", "PostCSS",
        "Webpack", "Vite", "Parcel", "Rollup", "Babel", "ESLint", "Prettier"
    ],
    
    "backend_framework": [
        "Django", "Flask", "FastAPI", "Express", "Express.js", "NestJS", 
        "Rails", "Ruby on Rails", "Laravel", "Spring", "Spring Boot", 
        "ASP.NET", "ASP.NET Core", ".NET", ".NET Core", "Sinatra", "Gin", 
        "Fiber", "Echo", "Phoenix", "Symfony", "CodeIgniter", "CakePHP", 
        "Slim", "Lumen", "Koa", "Hapi", "Strapi", "AdonisJS", "Sails.js",
        "Fastify", "Micronaut", "Quarkus", "Vert.x", "Play Framework",
        "Tornado", "Pyramid", "Bottle", "CherryPy", "Falcon"
    ],
    
    "database": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
        "Oracle", "SQL Server", "MariaDB", "DynamoDB", "Firebase", "Neo4j",
        "CouchDB", "InfluxDB", "Memcached", "SQLite", "CockroachDB", "RethinkDB",
        "ArangoDB", "TimescaleDB", "ClickHouse", "Snowflake", "BigQuery",
        "Redshift", "Azure SQL", "Cosmos DB", "FaunaDB", "PlanetScale",
        "Supabase", "Prisma", "TypeORM", "Sequelize", "Mongoose", "SQLAlchemy",
        "Hibernate", "Entity Framework", "Dapper", "Knex.js", "Drizzle"
    ],
    
    "devops": [
        "Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions", 
        "CircleCI", "Travis CI", "TeamCity", "Bamboo", "Azure DevOps",
        "Terraform", "Ansible", "Puppet", "Chef", "Vagrant", "Packer",
        "Prometheus", "Grafana", "ELK Stack", "Datadog", "New Relic",
        "Nagios", "Zabbix", "Consul", "Vault", "Nomad", "Rancher",
        "OpenShift", "ArgoCD", "Flux", "Helm", "Istio", "Linkerd",
        "Jaeger", "Zipkin", "Fluentd", "Logstash", "CloudFormation",
        "Pulumi", "CDK", "Serverless Framework", "SAM", "OpenTofu"
    ],
    
    "cloud": [
        "AWS", "Azure", "Google Cloud", "GCP", "Heroku", "DigitalOcean", 
        "Vercel", "Netlify", "Cloudflare", "Linode", "Vultr", "Render",
        "Fly.io", "Railway", "AWS EC2", "AWS S3", "AWS Lambda", "AWS RDS",
        "AWS ECS", "AWS EKS", "AWS SNS", "AWS SQS", "AWS CloudFront",
        "Azure Functions", "Azure Storage", "Azure AKS", "Google Kubernetes Engine",
        "Google Cloud Functions", "Cloud Run", "App Engine", "Compute Engine",
        "Cloud Storage", "BigQuery", "Pub/Sub", "Cloud SQL", "Firestore"
    ],
    
    "data_ml": [
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "Pandas", "NumPy",
        "Jupyter", "Apache Spark", "Hadoop", "Airflow", "MLflow", "Kubeflow",
        "Tableau", "Power BI", "Looker", "dbt", "Databricks", "SageMaker",
        "OpenCV", "NLTK", "spaCy", "Hugging Face", "LangChain", "OpenAI",
        "Matplotlib", "Seaborn", "Plotly", "D3.js", "Apache Beam", "Flink",
        "Storm", "Kafka", "RabbitMQ", "Celery", "Apache NiFi", "Prefect",
        "Dagster", "Great Expectations", "Apache Iceberg", "Delta Lake",
        "ML.NET", "Core ML", "TensorFlow Lite", "ONNX", "JAX"
    ],
    
    "mobile": [
        "React Native", "Flutter", "Ionic", "Xamarin", "SwiftUI", 
        "Jetpack Compose", "Expo", "NativeScript", "Cordova", "PhoneGap",
        "Android SDK", "iOS SDK", "Xcode", "Android Studio", "CocoaPods",
        "Gradle", "Maven", "Fastlane", "TestFlight", "Firebase",
        "Unity", "Unreal Engine", "ARKit", "ARCore", "Core Data",
        "Room", "Realm", "AsyncStorage", "SharedPreferences", "KeyChain"
    ],
    
    "testing": [
        "Jest", "Mocha", "Jasmine", "Cypress", "Selenium", "Puppeteer",
        "Playwright", "TestCafe", "Karma", "Protractor", "JUnit", "TestNG",
        "NUnit", "xUnit", "RSpec", "Minitest", "pytest", "unittest",
        "nose", "Behave", "Cucumber", "Postman", "Insomnia", "REST Assured",
        "SoapUI", "JMeter", "Gatling", "Locust", "Artillery", "K6",
        "Appium", "Espresso", "XCTest", "Detox", "Robot Framework"
    ],
    
    "other": [
        "Git", "GitHub", "GitLab", "Bitbucket", "SVN", "Mercurial",
        "JIRA", "Confluence", "Slack", "Microsoft Teams", "Notion",
        "Figma", "Sketch", "Adobe XD", "InVision", "Zeplin",
        "REST API", "GraphQL", "gRPC", "WebSockets", "Socket.io",
        "OAuth", "JWT", "SAML", "OpenID Connect", "Auth0",
        "Nginx", "Apache", "IIS", "HAProxy", "Varnish",
        "Linux", "Unix", "Windows Server", "macOS", "Ubuntu",
        "CentOS", "Debian", "Red Hat", "SUSE", "Alpine Linux",
        "Vim", "VS Code", "IntelliJ IDEA", "WebStorm", "PyCharm",
        "Sublime Text", "Atom", "Emacs", "Eclipse", "NetBeans",
        "Agile", "Scrum", "Kanban", "Waterfall", "DevOps",
        "CI/CD", "Microservices", "Serverless", "Event-Driven",
        "Domain-Driven Design", "Test-Driven Development", "TDD",
        "Behavior-Driven Development", "BDD", "Pair Programming",
        "Code Review", "Technical Documentation", "System Design",
        "Data Structures", "Algorithms", "Design Patterns",
        "SOLID Principles", "Clean Code", "Refactoring"
    ]
}

def seed_skills(db: Session = None):
    """
    Seed skills into the database
    """
    if db is None:
        db = SessionLocal()
    
    try:
        # Get existing skills to avoid duplicates
        existing_skills = db.query(SkillMaster.name).all()
        existing_skill_names = {skill[0].lower() for skill in existing_skills}
        
        logger.info(f"Found {len(existing_skill_names)} existing skills")
        
        added_count = 0
        skipped_count = 0
        
        # Add new skills
        for category, skills in SKILLS_DATA.items():
            for skill_name in skills:
                # Check if skill already exists (case-insensitive)
                if skill_name.lower() in existing_skill_names:
                    skipped_count += 1
                    continue
                
                # Create new skill
                skill = SkillMaster(
                    name=skill_name,
                    category=category,
                    source="seed",
                    is_verified=True
                )
                db.add(skill)
                added_count += 1
                
                # Add to existing set to prevent duplicates in same run
                existing_skill_names.add(skill_name.lower())
        
        db.commit()
        logger.info(f"✅ Successfully added {added_count} new skills")
        logger.info(f"⏭️  Skipped {skipped_count} existing skills")
        logger.info(f"📊 Total skills in database: {len(existing_skill_names)}")
        
        return added_count
        
    except Exception as e:
        logger.error(f"❌ Error seeding skills: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def update_skill_categories(db: Session = None):
    """
    Update categories for existing skills that might have wrong categories
    """
    if db is None:
        db = SessionLocal()
    
    try:
        updated_count = 0
        
        for category, skills in SKILLS_DATA.items():
            for skill_name in skills:
                # Find skill (case-insensitive)
                skill = db.query(SkillMaster).filter(
                    SkillMaster.name.ilike(skill_name)
                ).first()
                
                if skill and skill.category != category:
                    skill.category = category
                    updated_count += 1
        
        db.commit()
        logger.info(f"✅ Updated categories for {updated_count} skills")
        
    except Exception as e:
        logger.error(f"❌ Error updating categories: {str(e)}")
        db.rollback()
    finally:
        db.close()

def get_skill_stats(db: Session = None):
    """
    Get statistics about skills in database
    """
    if db is None:
        db = SessionLocal()
    
    try:
        from sqlalchemy import func
        
        # Total skills
        total = db.query(func.count(SkillMaster.id)).scalar()
        
        # Skills by category
        stats = db.query(
            SkillMaster.category,
            func.count(SkillMaster.id)
        ).group_by(SkillMaster.category).all()
        
        logger.info(f"\n📊 Skill Statistics:")
        logger.info(f"Total skills: {total}")
        logger.info(f"\nBy category:")
        for category, count in stats:
            logger.info(f"  {category}: {count}")
        
        return dict(stats)
        
    finally:
        db.close()

if __name__ == "__main__":
    # Run this script directly to seed skills
    logger.info("🌱 Starting skill seeding process...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Seed skills
    seed_skills()
    
    # Update categories
    update_skill_categories()
    
    # Show statistics
    get_skill_stats()