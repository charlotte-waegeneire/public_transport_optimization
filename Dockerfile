FROM docker.elastic.co/logstash/logstash:9.0.1

# Install the logstash-output-jdbc plugin
RUN bin/logstash-plugin install logstash-output-jdbc

# Include the JDBC driver
COPY postgresql-42.7.5.jar /usr/share/logstash/logstash-core/lib/jars/
