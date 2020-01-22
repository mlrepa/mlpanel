export default (previousState = 0, { type, state }) => {
    
    console.log(state)

    // if (type === 'BITCOIN_RATE_RECEIVED') {
    //     return payload.rate;
    // }
    return Object.assign({}, state, {
                type: "project_id",
                state:  123,
            }
      )
}