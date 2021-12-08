FROM ubuntu:latest as build
RUN apt-get update && apt-get install -y build-essential wget
RUN wget https://www.math.uwaterloo.ca/tsp/concorde/downloads/codes/src/co031219.tgz
RUN tar -xf co031219.tgz
RUN cd concorde && ./configure && make
# TODO: try to build the cplex

FROM ubuntu:latest
RUN apt-get update && apt-get install -y python3 python3-pyqt5 ca-certificates
COPY . .
COPY --from=build /concorde/TSP/concorde concorde

CMD ["/usr/bin/python3", "main.py"]