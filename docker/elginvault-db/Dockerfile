FROM timescale/timescaledb:latest-pg17

ARG PROJECT_ROOT

COPY create_tables.sql ./create_tables.sql
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 5432
