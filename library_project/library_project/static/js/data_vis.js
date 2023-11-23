
function parseResponse(data){
    let jsonLike = data.replace(/\(/g, '[').replace(/\)/g, ']');  
    // Replace single quotes with double quotes to make it valid JSON
    jsonLike = jsonLike.replace(/'/g, '"');
    // console.log(jsonLike);
    let result = JSON.parse(jsonLike);
    const arrayOfJSON = result.map(([id, name, address, email]) => ({
                             id,
                             name,
                             address,
                             email
    }));
    console.log(arrayOfJSON);
    return arrayOfJSON;
}

function buildTable(parseddata) {
const container = document.getElementById('table-container');

const table = document.createElement('table');

const headerRow = document.createElement('tr');

const headers = ['ID', 'Name', 'Address', 'Email'];

// Loop through the headers and create header cells
headers.forEach(headerText => {
    const headerCell = document.createElement('th');
    headerCell.textContent = headerText;
    headerRow.appendChild(headerCell);
});

// Append the header row to the table
table.appendChild(headerRow);

// Loop through the parsed data and create a row for each element
parseddata.forEach(element => {
    const row = document.createElement('tr');

    // Create data cells for each property (id, name, address, email)
    const idCell = document.createElement('td');
    idCell.textContent = element.id;
    row.appendChild(idCell);

    const nameCell = document.createElement('td');
    nameCell.textContent = element.name;
    row.appendChild(nameCell);

    const addressCell = document.createElement('td');
    addressCell.textContent = element.address;
    row.appendChild(addressCell);

    const emailCell = document.createElement('td');
    emailCell.textContent = element.email;
    row.appendChild(emailCell);

    // Append the row to the table
    table.appendChild(row);
});

// Append the table to the container
container.appendChild(table);
}
let fetched_data;
function get_data(table, csrf) {
    fetch("/db_ping/", {method: 'GET'})
    // , {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'text/plain',
    //         'X-CSRFToken': csrf, // Ensure this is the correct header for your server's CSRF token
    //     },
    //     body: table,
    //     credentials: 'include' // Include credentials if necessary for cookies
    // }
    // )
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error(`Network response was not ok: ${response.statusText}`);
        }
    })
    .then(data => {
        // Handle the data received from the server
        let parsed = parseResponse(data.message); // Depending on the response, you might not need to access .message
        buildTable(parsed);
    })
    .catch(error => {
        // Handle errors that may occur during the fetch
        console.error('Error:', error);
    });
}

// function get_data(table,csrf) {

//     fetch("/db_ping/", {
//         method:'POST',
        
//         headers: {
//         'table': table,
//         'csrfmiddlewaretoken':csrf,
//         }
//     }
    
//     )
//     .then(response => {
//         if (response.ok) {
//             return response.json(); // Parse the JSON response
//         } else {
//             throw new Error("Network response was not ok");
//         }
//     })
//     .then(data => {
//         // Handle the data received from the server
//         let parsed = parseResponse(data.message);
//         buildTable(parsed);
//         // let p = document.createElement("p");
//         // p.textContent = data.message;
//         // document.getElementById("div1").appendChild(p);
//     })
//     .catch(error => {
//         // Handle errors that may occur during the fetch
//         console.error('Error:', error);
//     });
// }