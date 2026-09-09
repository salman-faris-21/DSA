class MinStack {
private:
    stack<long long> st;
    long long mini;

public:
    MinStack() {
    }

    void push(int value) {
        if (st.empty()) {
            mini = value;
            st.push(value);
        } 
        else {
            if (value >= mini) {
                st.push(value);
            } 
            else {
                st.push(2LL * value - mini);
                mini = value;
            }
        }
    }

    void pop() {
        if (st.empty()) return;

        long long x = st.top();
        st.pop();

        if (x < mini) {
            mini = 2 * mini - x;
        }
    }

    int top() {
        long long x = st.top();

        if (x >= mini)
            return (int)x;

        return (int)mini;
    }

    int getMin() {
        return (int)mini;
    }
};