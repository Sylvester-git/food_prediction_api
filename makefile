run-local:
	uvicorn main:app --reload

gen_req_txt:
	pip freeze > requirements.txt
	@echo "requirements.txt file generated."