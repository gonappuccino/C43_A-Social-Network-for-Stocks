import psycopg2
from queries.setup import setup_queries
from flask import Flask, request

class Admin:
    conn = psycopg2.connect(
        host='localhost',
        database='postgres',
        user='postgres',
        password='2357'
    )
