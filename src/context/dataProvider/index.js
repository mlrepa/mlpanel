import { fetchUtils } from "react-admin";
import { stringify } from "query-string";
import Axios from "axios";

const apiUrl = "http://35.227.124.46:8080";
const httpClient = fetchUtils.fetchJson;

export default {
  getList: (resource, params) => {
    const { page, perPage } = params.pagination;
    const { field, order } = params.sort;

    const query = {
      _sort: field,
      _order: order,
      _start: (page - 1) * perPage,
      _end: page * perPage - 1,
      project_id: params.filter.project_id,
      experiment_id: params.filter.experiment_id
    };
    const url = `${apiUrl}/${resource}?${stringify(query)}`;

    return httpClient(url).then(({ headers, json }) => {
      if (!headers.has("X-Total-Count")) {
        throw new Error(
          "The X-Total-Count header is missing in the HTTP Response. The simple REST data provider expects responses for lists of resources to contain this header with the total number of results to build the pagination. If you are using CORS, did you declare Content-Range in the Access-Control-Expose-Headers header?"
        );
      }
      return {
        data: json,
        total: parseInt(
          headers
            .get("X-Total-Count")
            .split("/")
            .pop(),
          10
        )
      };
    });
  },

  getOne: (resource, params) => {
    const query = JSON.parse(localStorage.getItem("current_entities"));

    const url = `${apiUrl}/${resource}/${params.id}?${stringify(query)}`;

    return httpClient(url).then(({ json }) => ({
      data: json
    }));
  },

  getMany: (resource, params) => {
    const query = {
      filter: JSON.stringify({ id: params.ids })
    };
    const url = `${apiUrl}/${resource}?${stringify(query)}`;
    return httpClient(url).then(({ json }) => ({ data: json }));
  },

  getManyReference: (resource, params) => {
    const { page, perPage } = params.pagination;
    const { field, order } = params.sort;
    const query = {
      sort: JSON.stringify([field, order]),
      range: JSON.stringify([(page - 1) * perPage, page * perPage - 1]),
      filter: JSON.stringify({
        ...params.filter,
        [params.target]: params.id
      })
    };
    const url = `${apiUrl}/${resource}?${stringify(query)}`;

    return httpClient(url).then(({ headers, json }) => ({
      data: json,
      total: parseInt(
        headers
          .get("content-range")
          .split("/")
          .pop(),
        10
      )
    }));
  },

  update: (resource, params) =>
    httpClient(`${apiUrl}/${resource}/${params.id}`, {
      method: "PUT",
      body: JSON.stringify(params.data)
    }).then(({ json }) => ({ data: json })),

  updateMany: (resource, params) => {
    const query = {
      filter: JSON.stringify({ id: params.ids })
    };
    return httpClient(`${apiUrl}/${resource}?${stringify(query)}`, {
      method: "PUT",
      body: JSON.stringify(params.data)
    }).then(({ json }) => ({ data: json }));
  },

  create: (resource, params) => {
    const query = JSON.parse(localStorage.getItem("current_entities"));

    return httpClient(`${apiUrl}/${resource}?${stringify(query)}`, {
      method: "POST",
      headers: new Headers({
        "Content-Type": `application/x-www-form-urlencoded`
      }),
      body: JSON.stringify(params.data)
    }).then(({ json }) => ({
      data: { ...params.data, id: json.id }
    }));
  },

  delete: (resource, params) => {
    const query = JSON.parse(localStorage.getItem("current_entities"));

    return Axios.delete(
      `${apiUrl}/${resource}/${params.id}?project_id=${query.project_id}`
    ).then(res => ({ data: res.data }));
  },

  deleteMany: (resource, params) => {
    const query = {
      filter: JSON.stringify({ id: params.ids })
    };
    return httpClient(`${apiUrl}/${resource}?${stringify(query)}`, {
      method: "DELETE",
      body: JSON.stringify(params.data)
    }).then(({ json }) => ({ data: json }));
  }
};
