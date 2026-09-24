# AI search project
This file will describe the Plan and usage of the project. 
The name of the repo is the same as the book that inspired the project. 
The project itself is called ai_search_project. 
The Dev Plan is laid out in stages. 

# Stage 1 - Dev
0. Ask deepseek to create a django website with the needed pages
1. Ask NotebookLM to summarize each Chapter of the book AI Powered Search
2. Ask NotebookLM to create summary audios of each chapter of the book
3. Download docker desktop
4. Get django front-end running, test all links and refine where needed.
5. Get docker setup good so that it can run with a single command: 
./0_docker_compose.sh
6. Test at localhost:8000

# Stage 1 - Usage
1. Download project
2. Ensure you have a docker
3. ./0_docker_compose.sh
4. localhost:8000

# Stage 2 - Dev
1. Set up Solr
2. Set up a 2nd docker image, volume, container combo for the Solr in docker-compose.yml
3. Index the wayfair data
4. Create Django / Python code to call Solr
5. Ensure the iframe in the django app shows search box and search results
6. Commit code to github

# Stage 3 - Dev
1. Add OpenAI agents for the searching
2. Add chatbot to improve search experience

# Installation
1. call ai_search_project/1_docker_build.sh
2. wait for it to finish - it takes a few minutes
3. http://localhost:8000/


