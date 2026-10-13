import React from 'react';
import profile from './profile-svgrepo-com.svg'
import './Dashboard.css';

function Dashboard(){
    const emp = localStorage.getItem("userName");

    function toggleDropdown(){
        const dropdown = document.getElementById('dropdown');
        dropdown.classList.toggle('active');
    }

    function logout(){
        localStorage.clear();
    }

    async function rag_request(){
        const ragResponse = document.getElementById('p2');
        const ragQuery = document.getElementById('p1').value.trim();
        const btn = document.getElementById('submit-btn');

        if (!ragQuery) return;

        const responseCard = document.getElementById('response-card');
        responseCard.style.display = 'block';
        ragResponse.className = 'resp';
        ragResponse.style.display = 'block';
        ragResponse.innerText = 'Thinking…';
        btn.disabled = true;

        const token = localStorage.getItem("token");
        try {
            const res = await fetch('http://127.0.0.1:8000/user/query', {
                method: 'POST',
                headers: {
                    'accept': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_input: ragQuery }),
            });
            const result = await res.json();

            if (result.guardrail_blocked) {
                ragResponse.className = 'resp error';
                ragResponse.innerText = result.rag_response;
            } else {
                ragResponse.className = 'resp';
                ragResponse.innerHTML = result.rag_response;
            }
        }
        catch (error) {
            ragResponse.className = 'resp error';
            ragResponse.innerText = 'Network error — please try again.';
            console.error("Query Error:", error);
        }
        finally {
            btn.disabled = false;
        }
    }

    return(
        <div>
            <div className='nav-container'>
                <div className='Logo'>
                    <p>FinSolve</p>
                </div>
                <div className='Profile'>
                    <button className="profile-button" onClick={toggleDropdown}>
                        <img src={profile} alt="Profile"/>
                    </button>
                    <div className="dropdown-menu" id="dropdown">
                        <p>{emp}</p>
                        <a href="/" onClick={logout}>Logout</a>
                    </div>
                </div>
            </div>

            <div className='dashboard-body'>
                <div className='query-card'>
                    <h2>Ask FinSolve Assistant</h2>
                    <textarea
                        className="query-input"
                        placeholder='Enter your query…'
                        id='p1'
                    />
                    <div className='query-actions'>
                        <button
                            id='submit-btn'
                            className='query-button'
                            onClick={rag_request}
                        >Submit</button>
                    </div>
                </div>

                <div className='response-card' id='response-card' style={{display:'none'}}>
                    <div className='response-card-header'>Response</div>
                    <p className='resp' id='p2'></p>
                </div>
            </div>
        </div>
    )
}

export default Dashboard;