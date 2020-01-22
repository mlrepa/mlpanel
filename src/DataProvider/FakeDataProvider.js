import fakeDataProvider from 'ra-data-fakerest';

const dataProvider = fakeDataProvider({
  projects: [
    {
      "id": 0,
      "name": "Jedai Power Prediction",
      "status": "running",
      "mlflowUri": "http://0.0.0.0:5001/",
      "description": 'Test new project specs',
      "createdBy": 1,
      "createdAt": "2019-11-16T16:54:14.885Z"
    },
    {
      "id": 1,
      "name": "Dark side costs estimation",
      "status": "archived",
      "mlflowUri": "http://0.0.0.0:5001/",
      "description": 'Test new project specs',
      "createdBy": 0,
      "createdAt": "2019-11-16T16:54:14.885Z"
    },
    {
      "id": 2,
      "name": "Porgs' face recognition",
      "status": "terminated",
      "mlflowUri": "http://0.0.0.0:5001/",
      "description": 'Test new project specs',
      "createdBy": 1,
      "createdAt": "2019-11-16T16:54:14.885Z"
    },
  ],

  experiments: [
    { id: 0, projectId: 0, name: 'Experiment1', userId: 0 },
    { id: 1, projectId: 0, name: 'Experiment2', userId: 0 },
    { id: 2, projectId: 1, name: 'Experiment1', userId: 1 },
    { id: 3, projectId: 1, name: 'Experiment2', userId: 1 },
    { id: 4, projectId: 0, name: 'Experiment1', userId: 1 },
    { id: 5, projectId: 1, name: 'Experiment2', userId: 0 },
    { id: 6, projectId: 2, name: 'Experiment1', userId: 1 },
    { id: 7, projectId: 2, name: 'Experiment2', userId: 0 },
],
  users: [
    { userId: 0, name: 'Mikhail Rozhkov', username: 'mnrozhkov'},
    { userId: 1, name: 'Alex Antipin', username: 'alex_antipin' },
  ],

})


export default dataProvider 