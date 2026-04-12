import axios from "axios";

const vocsClient = axios.create({
  baseURL: "/vocs",
  timeout: 5000,
});

export default vocsClient;
