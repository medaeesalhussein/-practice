#include <iostream>
#include <cmath>
using namespace std;

// ---------- Subproject 1: Simple Calculator ----------
void simpleCalculator(int arr[], int n, int &sum, int &sub, int &mul) {
    sum = 0;
    sub = arr[0];
    mul = 1;

    for (int i = 0; i < n; i++) {
        sum += arr[i];
        mul *= arr[i];
        if (i > 0)
            sub -= arr[i];
    }
}

// ---------- Subproject 2: Equation Solver ----------
void linearEquation(double a, double b, double &x) {
    x = -b / a;
}

void quadraticEquation(double a, double b, double c, double &x1, double &x2, bool &hasRoot) {
    double delta = b*b - 4*a*c;
    if (delta < 0) {
        hasRoot = false;
    } else {
        hasRoot = true;
        x1 = (-b + sqrt(delta)) / (2*a);
        x2 = (-b - sqrt(delta)) / (2*a);
    }
}

// ---------- Subproject 3: Advanced Calculator ----------
int gcd(int a, int b) {
    while (b != 0) {
        int r = a % b;
        a = b;
        b = r;
    }
    return a;
}

int lcm(int a, int b) {
    return (a * b) / gcd(a, b);
}

long long combination(int n, int k) {
    long long res = 1;
    for (int i = 1; i <= k; i++) {
        res = res * (n - i + 1) / i;
    }
    return res;
}

// ---------- MAIN ----------
int main() {
    // Subproject 1
    int n;
    cout << "Enter number of elements: ";
    cin >> n;

    int arr[n];
    for (int i = 0; i < n; i++) {
        cin >> arr[i];
    }

    int sum, sub, mul;
    simpleCalculator(arr, n, sum, sub, mul);

    cout << "Sum: " << sum << endl;
    cout << "Subtraction: " << sub << endl;
    cout << "Multiplication: " << mul << endl;

    // Subproject 2
    int type;
    cout << "Enter equation type (1: linear, 2: quadratic): ";
    cin >> type;

    if (type == 1) {
        double a, b, x;
        cin >> a >> b;
        linearEquation(a, b, x);
        cout << "Root: " << x << endl;
    } else {
        double a, b, c, x1, x2;
        bool hasRoot;
        cin >> a >> b >> c;
        quadraticEquation(a, b, c, x1, x2, hasRoot);
        if (hasRoot)
            cout << "Roots: " << x1 << " , " << x2 << endl;
        else
            cout << "No real roots" << endl;
    }

    // Subproject 3
    int a, b;
    cout << "Enter two numbers: ";
    cin >> a >> b;

    cout << "GCD: " << gcd(a, b) << endl;
    cout << "LCM: " << lcm(a, b) << endl;

    int N, K;
    cout << "Enter N and K: ";
    cin >> N >> K;
    cout << "Combination: " << combination(N, K) << endl;

    return 0;
}
