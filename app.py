from flask import Flask, send_file, request, jsonify, make_response 
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import yaml
import os
import re
import copy

from flask_cors import CORS

def load_resume_content():
    """Load resume content from YAML file."""
    yaml_path = os.path.join(os.path.dirname(__file__), 'resume_content.yaml')
    with open(yaml_path, 'r') as file:
        return yaml.safe_load(file)

def create_resume():
    # Load resume content
    content = load_resume_content()
    
    # Create a buffer to store the PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=20,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=32,  # Reduced font size
        spaceAfter=6,  # Reduced space after title
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold'  # Using Helvetica Bold
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=8,
        spaceAfter=3,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=8.5,
        spaceAfter=1
    )

    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=8.5,
        spaceAfter=12,  # Increased space after contact info
        alignment=1  # Center alignment
    )

    position_style = ParagraphStyle(
        'PositionStyle',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        spaceAfter=1
    )

    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        spaceAfter=1
    )
    
    # Content elements
    elements = []
    
    # Header with more space
    name = f"{content['personal_info']['first_name']} {content['personal_info']['last_name']}"
    elements.append(Paragraph(name, title_style))
    elements.append(Spacer(1, 10))  # Reduced space between name and contact
    
    # Contact info with hyperlinked GitHub
    contact = content['personal_info']['contact']
    contact_text = (
        f"{contact['phone']} | {contact['email']} | "
        f'<link href="https://github.com/{contact["github"]}">GitHub: {contact["github"]}</link> | '
        f"Twitter: {contact['twitter']} | {contact['citizenship']}"
    )
    elements.append(Paragraph(contact_text, contact_style))
    
    # Summary
    elements.append(Paragraph("Summary", heading_style))
    elements.append(Paragraph(content['summary'], normal_style))
    
    # Technologies
    elements.append(Paragraph("Technologies", heading_style))
    tech = content['technologies']
    tech_items = [
        f"<b>Backend:</b> {tech['backend']}",
        f"<b>Frontend:</b> {tech['frontend']}",
        f"<b>DevOps:</b> {tech['devops']}",
        f"<b>Databases:</b> {tech['databases']}",
        f"<b>Soft Skills:</b> {tech['soft_skills']}"
    ]
    for item in tech_items:
        elements.append(Paragraph(item, normal_style))
    
    # Experience
    elements.append(Paragraph("Experience", heading_style))
    
    for exp in content['experience']:
        # Company and position in a table for better alignment
        position_text = exp['position']
        company_text = exp['company']
        location_text = exp['location']
        
        # Create a table for company info with location right-aligned
        company_table = Table([
            [Paragraph(position_text, position_style)],
            [
                Paragraph(company_text, company_style),
                Paragraph(location_text, ParagraphStyle(
                    'LocationStyle',
                    parent=company_style,
                    alignment=2  # Right alignment
                ))
            ]
        ], colWidths=[doc.width * 0.8, doc.width * 0.2])
        company_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
        ]))
        elements.append(company_table)
        
        elements.append(Paragraph(exp['duration'], normal_style))
        
        # Achievements with minimal spacing
        for achievement in exp['achievements']:
            elements.append(Paragraph("• " + achievement, normal_style))
        elements.append(Spacer(1, 2))  # Minimal space between experiences
    
    # Education
    elements.append(Paragraph("Education", heading_style))
    edu = content['education'][0]
    
    # Create a table for education with location right-aligned
    edu_table = Table([
        [Paragraph(edu['degree'], position_style)],
        [
            Paragraph(edu['institution'], normal_style),
            Paragraph("Irvine, CA", ParagraphStyle(
                'LocationStyle',
                parent=normal_style,
                alignment=2  # Right alignment
            ))
        ]
    ], colWidths=[doc.width * 0.8, doc.width * 0.2])
    edu_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
    ]))
    elements.append(edu_table)
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generatepdf():
    """Generate a PDF resume and save it to the current directory."""
    try:
        pdf_buffer = create_resume()
        with open('resume.pdf', 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print("PDF generated successfully! Saved as 'resume.pdf'")
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")

# Flask app (kept for web interface if needed)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route('/')
def index():
    return "Visit /download-pdf to get your resume"

@app.route('/download-pdf')
def download_pdf():
    try:
        pdf_buffer = create_resume()
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='resume.pdf'
        )
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500

def parse_job_description_keywords(text_blob):
    """Parse keywords from job description text blob."""
    # Control variable for limiting keyword matches to avoid over-optimization
    limit_keyword_matches = True
    max_match_percentage = 1.0  # 100% max match rate. change to lower if you want less
    
    
    # Proper capitalization mapping for technology terms
    proper_capitalization = {
        'mysql': 'MySQL',
        'postgresql': 'PostgreSQL',
        'mongodb': 'MongoDB',
        'dynamodb': 'DynamoDB',
        'bigquery': 'BigQuery',
        'nodejs': 'Node.js',
        'node.js': 'Node.js',
        'typescript': 'TypeScript',
        'javascript': 'JavaScript',
        'next.js': 'Next.js',
        'vue.js': 'Vue.js', 
        'react.js': 'React.js',
        'angular.js': 'Angular.js',
        'github': 'GitHub',
        'gitlab': 'GitLab',
        'bitbucket': 'BitBucket',
        'docker': 'Docker',
        'kubernetes': 'Kubernetes',
        'redis': 'Redis',
        'elasticsearch': 'Elasticsearch',
        'opensearch': 'OpenSearch',
        'cassandra': 'Cassandra',
        'nginx': 'Nginx',
        'apache': 'Apache',
        'tomcat': 'Tomcat',
        'jenkins': 'Jenkins',
        'terraform': 'Terraform',
        'ansible': 'Ansible',
        'kafka': 'Kafka',
        'rabbitmq': 'RabbitMQ',
        'activemq': 'ActiveMQ',
        'graphql': 'GraphQL',
        'grpc': 'gRPC',
        'websocket': 'WebSocket',
        'oauth': 'OAuth',
        'jwt': 'JWT',
        'html': 'HTML',
        'css': 'CSS',
        'sass': 'SASS',
        'scss': 'SCSS',
        'json': 'JSON',
        'xml': 'XML',
        'yaml': 'YAML',
        'sql': 'SQL',
        'nosql': 'NoSQL',
        'aws': 'AWS',
        'azure': 'Azure',
        'gcp': 'GCP',
        'api': 'API',
        'rest': 'REST',
        'soap': 'SOAP',
        'http': 'HTTP',
        'https': 'HTTPS',
        'tcp': 'TCP',
        'udp': 'UDP',
        'git': 'Git',
        'svn': 'SVN',
        'ci/cd': 'CI/CD',
        'cicd': 'CI/CD',
        'devops': 'DevOps',
        'sre': 'SRE',
        'orm': 'ORM',
        'mvc': 'MVC',
        'mvp': 'MVP',
        'spa': 'SPA',
        'pwa': 'PWA',
        'ssr': 'SSR',
        'csr': 'CSR',
        'dom': 'DOM',
        'ajax': 'AJAX',
        'cdn': 'CDN',
        'dns': 'DNS',
        'ssl': 'SSL',
        'tls': 'TLS',
        'vpc': 'VPC',
        'ec2': 'EC2',
        's3': 'S3',
        'rds': 'RDS',
        'ecs': 'ECS',
        'eks': 'EKS',
        'lambda': 'Lambda',
        'cloudformation': 'CloudFormation',
        'iam': 'IAM',
        'elk': 'ELK',
        'prometheus': 'Prometheus',
        'grafana': 'Grafana',
        'datadog': 'Datadog',
        'newrelic': 'New Relic',
        'splunk': 'Splunk',
        'kibana': 'Kibana',
        'logstash': 'Logstash',
        'fluentd': 'Fluentd',
        'jaeger': 'Jaeger',
        'zipkin': 'Zipkin',
        'istio': 'Istio',
        'linkerd': 'Linkerd',
        'consul': 'Consul',
        'vault': 'Vault',
        'helm': 'Helm',
        'openshift': 'OpenShift',
        'rancher': 'Rancher'
    }
    # Define comprehensive keyword mappings (no duplicates across categories)
    backend_keywords = [
        # Languages
        'python', 'java', 'golang', 'go', 'c++', 'c#', 'ruby', 'php', 'scala', 'kotlin', 
        'rust', 'swift', 'perl', 'haskell', 'clojure', 'erlang', 'elixir',
        # Frameworks/Libraries
        'spring', 'django', 'flask', 'fastapi', 'express', 'nest', 'gin', 'fiber',
        'rails', 'laravel', 'symfony', 'akka', 'vert.x', 'quarkus',
        # Web servers/Reverse proxies
        'nginx', 'apache', 'tomcat', 'jetty', 'gunicorn', 'uwsgi',
        # APIs & Communication
        'rest', 'graphql', 'grpc', 'soap', 'websocket', 'rpc',
        # Architecture patterns
        'microservices', 'serverless', 'lambda', 'event-driven', 'message-queue',
        # Messaging systems
        'kafka', 'rabbitmq', 'activemq', 'amazon sqs', 'pubsub', 'nats', 'zeromq',
        # Search & Analytics
        'elasticsearch', 'solr', 'lucene', 'algolia', 'opensearch',
        # Cache systems (when used as application cache)
        'redis', 'memcached', 'hazelcast'
    ]
    
    database_keywords = [
        # Relational databases
        'postgres', 'postgresql', 'mysql', 'mariadb', 'sqlite', 'oracle', 'sql server',
        'db2', 'sybase', 'teradata', 'cockroachdb', 'vitess',
        # NoSQL databases
        'mongodb', 'dynamodb', 'cassandra', 'couchbase', 'couchdb', 'neo4j', 'arangodb',
        'orientdb', 'riak', 'hbase', 'bigtable',
        # Cloud databases
        'firestore', 'cosmos db', 'documentdb', 'aurora', 'redshift',
        # Data warehouses
        'snowflake', 'bigquery', 'databricks', 'clickhouse', 'vertica',
        # Time series databases
        'influxdb', 'timescaledb', 'prometheus tsdb',
        # Graph databases
        'dgraph', 'tigergraph', 'amazon neptune',
        # General terms
        'sql', 'nosql', 'hibernate', 'sequelize', 'prisma',
        'knex', 'typeorm', 'sqlalchemy', 'activerecord'
    ]
    
    devops_keywords = [
        # Cloud platforms
        'aws', 'azure', 'gcp', 'google cloud', 'amazon web services', 'alibaba cloud',
        'digitalocean', 'linode', 'vultr', 'heroku', 'vercel', 'netlify',
        # Containerization & orchestration
        'docker', 'kubernetes', 'k8s', 'openshift', 'rancher', 'docker swarm',
        'containerd', 'podman', 'buildah',
        # Infrastructure as Code
        'terraform', 'pulumi', 'cloudformation', 'cdk', 'arm templates',
        # Configuration management
        'ansible', 'puppet', 'chef', 'saltstack',
        # CI/CD
        'jenkins', 'gitlab ci', 'github actions', 'circleci', 'travis ci', 'bamboo',
        'teamcity', 'azure devops', 'spinnaker', 'argo cd', 'flux',
        'ci/cd', 'cicd', 'continuous integration', 'continuous deployment',
        # Monitoring & observability
        'prometheus', 'grafana', 'datadog', 'newrelic', 'splunk', 'elk', 'elastic stack',
        'kibana', 'logstash', 'fluentd', 'jaeger', 'zipkin', 'opentelemetry',
        'nagios', 'zabbix', 'pingdom', 'uptime robot',
        # Service mesh & networking
        'istio', 'linkerd', 'consul', 'envoy', 'traefik', 'haproxy',
        # Version control
        'git', 'github', 'gitlab', 'bitbucket', 'svn', 'perforce',
        # # Package managers & registries
        # 'npm', 'yarn', 'pip', 'conda', 'maven', 'gradle', 'nexus', 'artifactory',
        # Security & secrets
        'vault', 'secrets manager', 'parameter store', 'keycloak',
        # General terms
        # 'devops', 'sre', 'site reliability', 'infrastructure', 'deployment',
        # 'automation', 'logging', 'monitoring', 'observability', 'scalability'
    ]
    
    frontend_keywords = [
        # Core technologies
        'html', 'css', 'javascript', 'typescript',
        # Frameworks & libraries
        'react', 'vue', 'angular',#'svelte', 'solid', 'qwik', 'lit', 'stencil',
        'ember',# 'backbone', 'knockout', 'aurelia',
        # React ecosystem
        'next.js', 'gatsby', 'remix', 'create-react-app', 'vite',
        # Vue ecosystem
        'nuxt', 'gridsome', 'quasar',
        # State management
        'redux', 'mobx', 'zustand', 'recoil', 'vuex', 'pinia', 'ngrx',
        # Build tools
        'webpack', 'rollup', 'parcel', 'esbuild', 'snowpack', 'turbopack',
        # CSS frameworks & preprocessors
        'tailwind', 'bootstrap', 'bulma', 'foundation', 'semantic ui', 'ant design',
        'material ui', 'chakra ui', 'sass', 'scss', 'stylus', 'styled-components',
        # Testing
        'jest', 'cypress', 'playwright', 'selenium',
        # Package managers
        'node.js', 'nodejs', 'npm', 'yarn', 'pnpm',
    ]
    
    soft_skills_keywords = [
        # Leadership & management
        'leadership', 'management', 'team lead', 'tech lead', 'engineering manager',
        'people management', 'mentoring', 'coaching', 'training',
        # Project & process management
        'project management', 'program management', 'product management',
        'agile', 'scrum', 'kanban', 'lean', 'waterfall', 'sprint planning',
        'retrospectives', 'standup', 'estimation', 'roadmapping',
        # Communication & collaboration
        'collaboration', 'teamwork', 'cross-functional',
        'stakeholder management', 'client relations', 'presentation',
        'documentation', 'technical writing', 'requirements gathering',
        # Problem solving & analysis
        'problem solving', 'analytical', 'critical thinking', 'troubleshooting',
        'debugging', 'root cause analysis', 'decision making',
        # Strategy & planning
        'strategic planning', 'architecture design', 'system design',
        'capacity planning', 'risk assessment', 'vendor management',
        # Quality & processes
        'code review', 'quality assurance', 'testing strategy',
        'performance optimization', 'security awareness',
        # Adaptability & learning
        'adaptability', 'learning agility', 'innovation', 'creativity',
        'continuous improvement', 'growth mindset'
    ]
    
    # Convert to lowercase for matching
    text_lower = text_blob.lower()
    
    # Extract keywords using word boundaries for exact matching
    found_backend = [kw for kw in backend_keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
    found_databases = [kw for kw in database_keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
    found_devops = [kw for kw in devops_keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
    found_frontend = [kw for kw in frontend_keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
    found_soft_skills = [kw for kw in soft_skills_keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
    
    # Limit keyword matches to avoid over-optimization (80% max)
    if limit_keyword_matches:
        import random
        
        # Calculate max keywords per category (80% of found keywords)
        max_backend = max(1, int(len(found_backend) * max_match_percentage))
        max_databases = max(1, int(len(found_databases) * max_match_percentage)) 
        max_devops = max(1, int(len(found_devops) * max_match_percentage))
        max_frontend = max(1, int(len(found_frontend) * max_match_percentage))
        max_soft_skills = max(1, int(len(found_soft_skills) * max_match_percentage))
        
        # Randomly select subset if we have too many matches
        if len(found_backend) > max_backend:
            found_backend = random.sample(found_backend, max_backend)
        if len(found_databases) > max_databases:
            found_databases = random.sample(found_databases, max_databases)
        if len(found_devops) > max_devops:
            found_devops = random.sample(found_devops, max_devops)
        if len(found_frontend) > max_frontend:
            found_frontend = random.sample(found_frontend, max_frontend)
        if len(found_soft_skills) > max_soft_skills:
            found_soft_skills = random.sample(found_soft_skills, max_soft_skills)
    
    # Custom logic: Only add C++ if Go and Java are NOT in the job description  
    if 'c++' in found_backend and ('go' in text_lower or 'golang' in text_lower or 'java' in text_lower):
        found_backend = [kw for kw in found_backend if kw != 'c++']
    
    return {
        'backend': found_backend,
        'databases': found_databases, 
        'devops': found_devops,
        'frontend': found_frontend,
        'soft_skills': found_soft_skills
    }

def merge_skills_no_duplicates(existing_skills, new_skills, all_technologies_text=""):
    """Merge skill lists removing duplicates (case insensitive)."""
    # Proper capitalization mapping for technology terms
    proper_capitalization = {
        'mysql': 'MySQL', 'postgresql': 'PostgreSQL', 'mongodb': 'MongoDB',
        'dynamodb': 'DynamoDB', 'bigquery': 'BigQuery', 'nodejs': 'Node.js',
        'node.js': 'Node.js', 'typescript': 'TypeScript', 'javascript': 'JavaScript',
        'next.js': 'Next.js', 'vue.js': 'Vue.js', 'react.js': 'React.js',
        'github': 'GitHub', 'gitlab': 'GitLab', 'docker': 'Docker',
        'kubernetes': 'Kubernetes', 'redis': 'Redis', 'elasticsearch': 'Elasticsearch',
        'nginx': 'Nginx', 'apache': 'Apache', 'jenkins': 'Jenkins',
        'terraform': 'Terraform', 'ansible': 'Ansible', 'kafka': 'Kafka',
        'rabbitmq': 'RabbitMQ', 'graphql': 'GraphQL', 'grpc': 'gRPC',
        'websocket': 'WebSocket', 'html': 'HTML', 'css': 'CSS', 'sass': 'SASS',
        'scss': 'SCSS', 'sql': 'SQL', 'nosql': 'NoSQL', 'aws': 'AWS',
        'azure': 'Azure', 'gcp': 'GCP', 'api': 'API', 'rest': 'REST',
        'git': 'Git', 'ci/cd': 'CI/CD', 'devops': 'DevOps', 'orm': 'ORM',
        'spa': 'SPA', 'pwa': 'PWA', 'dom': 'DOM', 'prometheus': 'Prometheus',
        'grafana': 'Grafana', 'datadog': 'Datadog'
    }
    
    # Split existing skills by comma, strip whitespace and punctuation
    existing_list = []
    existing_lower = []
    
    for skill in existing_skills.split(','):
        # Strip whitespace and remove trailing punctuation
        cleaned_skill = skill.strip().rstrip('.')
        if cleaned_skill:  # Only add non-empty skills
            existing_list.append(cleaned_skill)
            existing_lower.append(cleaned_skill.lower())
    
    # Create a text blob of all existing skills for broader duplicate checking
    existing_text_blob = existing_skills.lower()
    
    # Also include all technologies text for cross-category duplicate checking
    all_tech_lower = all_technologies_text.lower()
    
    # Add new skills that don't already exist
    merged_skills = existing_list.copy()
    for new_skill in new_skills:
        cleaned_new_skill = new_skill.strip().rstrip('.')
        if cleaned_new_skill:
            # Check both individual skill match, current category, and ALL technologies
            skill_lower = cleaned_new_skill.lower()
            if (skill_lower not in existing_lower and 
                skill_lower not in existing_text_blob and
                skill_lower not in all_tech_lower):
                # Apply proper capitalization if available, otherwise use title case
                proper_skill = proper_capitalization.get(skill_lower, cleaned_new_skill.title())
                merged_skills.append(proper_skill)
                existing_lower.append(skill_lower)
                existing_text_blob += f", {skill_lower}"  # Add to blob for subsequent checks
    
    return ', '.join(merged_skills)

@app.route('/download-resume-custom', methods=['POST'])
def download_resume_custom():
    """
    Custom resume endpoint that:
    1. Takes a job description text blob
    2. Parses keywords from it
    3. Temporarily adds new keywords to resume
    4. Generates PDF with enhanced resume
    5. Reverts back to original content
    """
    yaml_path = os.path.join(os.path.dirname(__file__), 'resume_content.yaml')
    
    try:
        # Load existing resume content
        original_content = load_resume_content()
        
        # Get the job description from request body
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        
        if not data or 'job_description' not in data:
            return jsonify({"error": "JSON body with 'job_description' field is required"}), 400
        
        job_description = data['job_description']
        
        # Parse keywords from job description
        parsed_keywords = parse_job_description_keywords(job_description)
        
        # Create modified content with merged skills
        modified_content = copy.deepcopy(original_content)
        tech = modified_content['technologies']
        
        # Create a combined text of all current technologies for cross-category deduplication
        all_technologies_text = ' '.join([
            tech['backend'],
            tech['databases'], 
            tech['devops'],
            tech['frontend'],
            tech['soft_skills']
        ])
        
        # Merge skills avoiding duplicates (now checking across all categories)
        if parsed_keywords['backend']:
            tech['backend'] = merge_skills_no_duplicates(tech['backend'], parsed_keywords['backend'], all_technologies_text)
        if parsed_keywords['databases']:
            tech['databases'] = merge_skills_no_duplicates(tech['databases'], parsed_keywords['databases'], all_technologies_text)
        if parsed_keywords['devops']:
            tech['devops'] = merge_skills_no_duplicates(tech['devops'], parsed_keywords['devops'], all_technologies_text)
        if parsed_keywords['frontend']:
            tech['frontend'] = merge_skills_no_duplicates(tech['frontend'], parsed_keywords['frontend'], all_technologies_text)
        if parsed_keywords['soft_skills']:
            tech['soft_skills'] = merge_skills_no_duplicates(tech['soft_skills'], parsed_keywords['soft_skills'], all_technologies_text)
        
        # Temporarily save modified content to YAML
        with open(yaml_path, 'w') as file:
            yaml.dump(modified_content, file, default_flow_style=False)
        
        # Generate PDF with modified content
        pdf_buffer = create_resume()
        
        # Revert back to original content
        with open(yaml_path, 'w') as file:
            yaml.dump(original_content, file, default_flow_style=False)

        # Create response
        response = make_response(pdf_buffer.getvalue())
        response.headers.set("Content-Type", "application/pdf")
        response.headers.set(
            "Content-Disposition",
            "attachment",
            filename="customized_resume.pdf"
        )
        return response

        
    except Exception as e:
        # Ensure we revert back to original content even if error occurs
        try:
            with open(yaml_path, 'w') as file:
                yaml.dump(original_content, file, default_flow_style=False)
        except:
            pass
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'generatepdf':
        generatepdf()
    else:
        app.run(debug=True, host='0.0.0.0', port=5001)